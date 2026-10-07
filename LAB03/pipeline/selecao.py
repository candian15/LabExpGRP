"""Seleção dos repositórios da amostra: busca, metadados e filtros de inclusão.

Regras do enunciado (seções 3 e 4):
- os candidatos vêm da busca ``stars:>1000``. A busca devolve no máximo 1.000
  resultados por consulta, então ela é fatiada por faixa de estrelas
  (``stars:1000..2000``, ``stars:2000..5000``, ...) e, se quiser, por linguagem;
- repositório sem GitHub Actions (``total_count = 0`` em ``/actions/workflows``)
  é descartado antes de se gastar qualquer outra chamada com ele;
- entra na amostra quem tiver, dentro da janela, pelo menos 5 releases
  publicadas e 50 workflow runs válidos no default branch.

Os filtros são aplicados nessa ordem e param no primeiro que falha: assim cada
repositório recebe no máximo um motivo de descarte, que é o que ``pipeline.funil``
agrega na tabela do funil.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from metricas.cfr import runs_validos
from pipeline.coleta_releases import listar_releases, releases_na_janela
from pipeline.coleta_runs import coletar_runs, repo_usa_actions
from pipeline.github_client import GitHubClient, NaoEncontrado

log = logging.getLogger(__name__)

TETO_BUSCA = 1000  # máximo de resultados que a busca devolve por consulta

CAMPOS_META = [
    "repo",
    "estrelas",
    "linguagem",
    "default_branch",
    "criado_em",
    "idade_anos",
    "contribuidores",
]


def consulta(faixa: str = ">1000", linguagem: str | None = None) -> str:
    """Monta o ``q`` da busca. ``faixa`` é o trecho de estrelas, ex.: ``1000..2000``."""
    q = f"stars:{faixa}"
    if linguagem:
        q += f" language:{linguagem}"
    return q


def _buscar_uma(gh: GitHubClient, q: str, limite: int) -> list[dict]:
    itens: list[dict] = []
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 100}
    for pagina in gh.paginar("/search/repositories", params):
        total = pagina.get("total_count", 0)
        if not itens and total > limite:
            log.warning(
                "'%s' tem %d resultados e a busca devolve no máximo %d; "
                "fatie essa faixa em faixas menores no config.yaml",
                q, total, limite,
            )
        itens.extend(pagina.get("items", []))
        if len(itens) >= limite:
            break
    log.info("'%s': %d candidatos", q, min(len(itens), limite))
    return itens[:limite]


def buscar_candidatos(
    gh: GitHubClient,
    faixas: list[str] | tuple[str, ...] = (">1000",),
    linguagens: list[str] | tuple[str, ...] = (),
    limite_por_consulta: int = TETO_BUSCA,
) -> list[dict]:
    """Candidatos de todas as faixas, sem repetição, do mais para o menos estrelado."""
    encontrados: dict[str, dict] = {}
    for faixa in faixas:
        for linguagem in linguagens or [None]:
            for repo in _buscar_uma(gh, consulta(faixa, linguagem), limite_por_consulta):
                encontrados.setdefault(repo["full_name"], repo)
    return sorted(encontrados.values(), key=lambda r: -(r.get("stargazers_count") or 0))


def metadados(repo: dict, referencia: date) -> dict:
    """Metadados do JSON de ``/repos/{owner}/{repo}``.

    A idade é medida até ``referencia`` (o fim da janela, e não "hoje") para que
    rodar o pipeline em outro dia dê o mesmo número.
    """
    criado = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
    criado = criado.astimezone(timezone.utc).date()
    return {
        "repo": repo["full_name"],
        "estrelas": repo.get("stargazers_count"),
        "linguagem": repo.get("language"),
        "default_branch": repo.get("default_branch"),
        "criado_em": criado.isoformat(),
        "idade_anos": round((referencia - criado).days / 365.25, 2),
    }


def contar_contribuidores(gh: GitHubClient, owner: str, repo: str) -> int | None:
    """Nº de contribuidores (quartis da RQ 06), sem baixar a lista inteira."""
    try:
        return gh.contar_por_link(f"/repos/{owner}/{repo}/contributors", {"anon": "true"})
    except NaoEncontrado:
        return None


def avaliar(
    gh: GitHubClient,
    repo: dict,
    inicio: date,
    fim: date,
    min_releases: int = 5,
    min_runs: int = 50,
    contribuidores: bool = False,
) -> dict:
    """Metadados e resultado dos filtros de inclusão de um candidato.

    ``motivo_descarte`` vazio significa que o repositório entra na amostra. A
    chave ``runs`` traz os runs já coletados, para as métricas não precisarem
    coletá-los de novo.
    """
    linha = metadados(repo, fim)
    linha.update(n_releases=0, n_runs_validos=0, motivo_descarte="", runs=[])
    owner, nome = linha["repo"].split("/", 1)

    if not repo_usa_actions(gh, owner, nome):
        linha["motivo_descarte"] = "sem_actions"
        return linha

    na_janela = releases_na_janela(listar_releases(gh, owner, nome), inicio, fim)
    linha["n_releases"] = len(na_janela)
    if len(na_janela) < min_releases:
        linha["motivo_descarte"] = "poucas_releases"
        return linha

    runs = coletar_runs(gh, owner, nome, linha["default_branch"], inicio, fim)
    linha["n_runs_validos"] = len(runs_validos(runs))
    if linha["n_runs_validos"] < min_runs:
        linha["motivo_descarte"] = "poucos_runs"
        return linha

    linha["runs"] = runs
    if contribuidores:
        linha["contribuidores"] = contar_contribuidores(gh, owner, nome)
    return linha
