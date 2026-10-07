"""Cliente HTTP da API REST do GitHub usado por todo o pipeline.

Responsabilidades (seção 7 do enunciado):
- autenticação via variável de ambiente GITHUB_TOKEN (nunca commitar o token);
- cache local em disco: cada resposta vira um JSON em ``cache/``, então rodar
  de novo continua de onde parou, sem gastar cota;
- paginação seguindo o cabeçalho ``Link`` (rel="next");
- espera automática quando o rate limit acaba (X-RateLimit-Remaining/Reset);
- retry com backoff exponencial (1s, 2s, 4s, 8s...) em erros 5xx e de rede.

Não usa nenhuma biblioteca de acesso ao GitHub (PyGithub etc.), só ``requests``.

Uso básico::

    from pipeline.github_client import GitHubClient

    gh = GitHubClient()                      # lê GITHUB_TOKEN do ambiente
    repo = gh.get("/repos/psf/requests")     # um único objeto
    for pagina in gh.paginar("/repos/psf/requests/releases", {"per_page": 100}):
        ...                                  # cada página é o JSON cru
    releases = gh.listar("/repos/psf/requests/releases")  # junta todas as páginas
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import urlencode

import requests

log = logging.getLogger(__name__)

API_URL = "https://api.github.com"

# Chaves em que endpoints "envelopados" guardam a lista de itens.
CHAVES_DE_ITENS = ("items", "workflow_runs", "workflows", "commits", "jobs", "artifacts")


class ErroGitHub(Exception):
    """Erro definitivo da API (depois de esgotar as tentativas)."""

    def __init__(self, status: int, url: str, mensagem: str = ""):
        super().__init__(f"HTTP {status} em {url}: {mensagem}")
        self.status = status
        self.url = url


class NaoEncontrado(ErroGitHub):
    """404 — ex.: compare entre tags apagadas/reescritas (ver FAQ do enunciado)."""


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        cache_dir: str | Path = "cache",
        max_tentativas: int = 6,
        timeout: float = 30.0,
        session: requests.Session | None = None,
        dormir: Callable[[float], None] = time.sleep,
        agora: Callable[[], float] = time.time,
    ):
        token = token or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError(
                "Defina a variável de ambiente GITHUB_TOKEN com um token do GitHub "
                "(ex.: export GITHUB_TOKEN=ghp_...)."
            )
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_tentativas = max_tentativas
        self.timeout = timeout
        self._dormir = dormir
        self._agora = agora
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "lab03-dora-pipeline",
            }
        )
        # Contadores úteis para o README/log da coleta.
        self.chamadas_api = 0
        self.acertos_cache = 0

    # ------------------------------------------------------------------ cache
    @staticmethod
    def _montar_url(caminho_ou_url: str, params: dict | None) -> str:
        url = caminho_ou_url if caminho_ou_url.startswith("http") else API_URL + caminho_ou_url
        if params:
            sep = "&" if "?" in url else "?"
            url = url + sep + urlencode(sorted(params.items()))
        return url

    def _arquivo_cache(self, url: str) -> Path:
        chave = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / chave[:2] / f"{chave}.json"

    def _ler_cache(self, url: str) -> dict | None:
        arq = self._arquivo_cache(url)
        if not arq.exists():
            return None
        try:
            return json.loads(arq.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None  # arquivo corrompido: refaz a chamada

    def _gravar_cache(self, url: str, registro: dict) -> None:
        arq = self._arquivo_cache(url)
        arq.parent.mkdir(parents=True, exist_ok=True)
        tmp = arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(registro), encoding="utf-8")
        tmp.replace(arq)  # escrita atômica: Ctrl+C não deixa JSON pela metade

    # ------------------------------------------------------------- requisição
    def _esperar_rate_limit(self, resp: requests.Response) -> bool:
        """Espera se a cota acabou. Retorna True se a requisição deve ser refeita."""
        restante = resp.headers.get("X-RateLimit-Remaining")
        reset = resp.headers.get("X-RateLimit-Reset")
        retry_after = resp.headers.get("Retry-After")

        if resp.status_code in (403, 429) and retry_after:  # rate limit secundário
            espera = float(retry_after) + 1
            log.warning("Rate limit secundário; aguardando %.0fs", espera)
            self._dormir(espera)
            return True

        if restante is not None and int(restante) == 0 and reset:
            espera = max(0.0, float(reset) - self._agora()) + 2
            log.warning("Cota da API esgotada; aguardando %.0fs até o reset", espera)
            self._dormir(espera)
            # Se a resposta veio com erro por causa da cota, refaz; se veio 200, já serve.
            return resp.status_code in (403, 429)
        return False

    def _requisitar(self, url: str) -> dict:
        espera = 1.0
        for tentativa in range(1, self.max_tentativas + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                if tentativa == self.max_tentativas:
                    raise
                log.warning("Erro de rede (%s); tentativa %d, aguardando %.0fs", e, tentativa, espera)
                self._dormir(espera)
                espera *= 2
                continue

            self.chamadas_api += 1
            if self._esperar_rate_limit(resp):
                continue

            if resp.status_code >= 500:
                if tentativa == self.max_tentativas:
                    raise ErroGitHub(resp.status_code, url, resp.text[:200])
                log.warning("HTTP %d; tentativa %d, aguardando %.0fs", resp.status_code, tentativa, espera)
                self._dormir(espera)
                espera *= 2
                continue

            if resp.status_code == 404:
                return {"status": 404, "data": None, "next": None}
            if resp.status_code >= 400:
                raise ErroGitHub(resp.status_code, url, resp.text[:200])

            return {
                "status": resp.status_code,
                "data": resp.json(),
                "next": resp.links.get("next", {}).get("url"),
                "last": resp.links.get("last", {}).get("url"),
            }
        raise ErroGitHub(-1, url, "tentativas esgotadas")

    def _obter_registro(self, url: str, usar_cache: bool = True) -> dict:
        if usar_cache:
            registro = self._ler_cache(url)
            if registro is not None:
                self.acertos_cache += 1
                return registro
        registro = self._requisitar(url)
        if usar_cache:
            self._gravar_cache(url, registro)  # 404 também vai pro cache: não repete
        return registro

    # ---------------------------------------------------------------- pública
    def get(self, caminho_ou_url: str, params: dict | None = None, usar_cache: bool = True) -> Any:
        """GET de uma única página. Levanta NaoEncontrado em 404."""
        url = self._montar_url(caminho_ou_url, params)
        registro = self._obter_registro(url, usar_cache)
        if registro["status"] == 404:
            raise NaoEncontrado(404, url)
        return registro["data"]

    def paginar(self, caminho_ou_url: str, params: dict | None = None) -> Iterator[Any]:
        """Gera o JSON de cada página, seguindo o cabeçalho Link até o fim."""
        url: str | None = self._montar_url(caminho_ou_url, params)
        while url:
            registro = self._obter_registro(url)
            if registro["status"] == 404:
                raise NaoEncontrado(404, url)
            yield registro["data"]
            url = registro.get("next")

    def listar(self, caminho_ou_url: str, params: dict | None = None) -> list:
        """Junta os itens de todas as páginas numa lista só.

        Funciona tanto para endpoints que devolvem lista crua (``/releases``)
        quanto para os envelopados (``workflow_runs``, ``items``, ``commits``...).
        """
        params = {"per_page": 100, **(params or {})}
        itens: list = []
        for pagina in self.paginar(caminho_ou_url, params):
            itens.extend(extrair_itens(pagina))
        return itens

    def contar_por_link(self, caminho: str, params: dict | None = None) -> int:
        """Conta itens sem baixar tudo: pede per_page=1 e lê a última página no Link.

        Ex.: ``gh.contar_por_link(f"/repos/{o}/{r}/contributors", {"anon": "true"})``.
        """
        url = self._montar_url(caminho, {**(params or {}), "per_page": 1})
        registro = self._obter_registro(url)
        if registro["status"] == 404:
            raise NaoEncontrado(404, url)
        ultima = registro.get("last")
        if ultima:
            m = re.search(r"[?&]page=(\d+)", ultima)
            if m:
                return int(m.group(1))
        return len(extrair_itens(registro["data"]))

    def rate_limit(self) -> dict:
        """Situação atual da cota (não consome cota e nunca usa cache)."""
        return self.get("/rate_limit", usar_cache=False)


def extrair_itens(pagina: Any) -> list:
    if pagina is None:
        return []
    if isinstance(pagina, list):
        return pagina
    for chave in CHAVES_DE_ITENS:
        if chave in pagina and isinstance(pagina[chave], list):
            return pagina[chave]
    return []
