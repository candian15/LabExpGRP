from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

from pipeline.github_client import GitHubClient, NaoEncontrado

log = logging.getLogger(__name__)


def _data(valor: str) -> datetime:
    dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def listar_releases(gh: GitHubClient, owner: str, repo: str) -> list[dict]:
    releases = []
    for r in gh.listar(f"/repos/{owner}/{repo}/releases"):
        if r.get("draft") or not r.get("published_at"):
            continue
        releases.append(
            {
                "tag_name": r["tag_name"],
                "published_at": r["published_at"],
                "prerelease": bool(r.get("prerelease")),
                "html_url": r.get("html_url"),
            }
        )
    releases.sort(key=lambda r: _data(r["published_at"]))
    return releases


def releases_na_janela(
    releases: list[dict], inicio: date, fim: date, incluir_prerelease: bool = False
) -> list[dict]:
    return [
        r
        for r in releases
        if (incluir_prerelease or not r["prerelease"])
        and inicio <= _data(r["published_at"]).date() <= fim
    ]


def listar_commits_entre(gh: GitHubClient, owner: str, repo: str, base: str, head: str) -> list[dict]:
    caminho = f"/repos/{owner}/{repo}/compare/{quote(base, safe='/')}...{quote(head, safe='/')}"
    return [
        {"sha": c["sha"], "data": c["commit"]["author"]["date"]}
        for c in gh.listar(caminho)
    ]


def coletar_releases(
    gh: GitHubClient,
    owner: str,
    repo: str,
    inicio: date,
    fim: date,
    incluir_prerelease: bool = False,
) -> dict:
    todas = listar_releases(gh, owner, repo)
    unidades = [r for r in todas if incluir_prerelease or not r["prerelease"]]
    comparacoes = []
    ignoradas_404 = 0
    for i, r in enumerate(unidades):
        if not inicio <= _data(r["published_at"]).date() <= fim:
            continue
        anterior = unidades[i - 1]["tag_name"] if i > 0 else None
        item = {
            "tag_name": r["tag_name"],
            "published_at": r["published_at"],
            "prerelease": r["prerelease"],
            "anterior": anterior,
            "status": "ok",
            "commits": [],
        }
        if anterior is None:
            item["status"] = "primeira"
        else:
            try:
                item["commits"] = listar_commits_entre(gh, owner, repo, anterior, r["tag_name"])
            except NaoEncontrado:
                log.warning(
                    "%s/%s: compare %s...%s deu 404; release ignorada no lead time",
                    owner, repo, anterior, r["tag_name"],
                )
                item["status"] = "404"
                ignoradas_404 += 1
        comparacoes.append(item)
    return {
        "repo": f"{owner}/{repo}",
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "incluir_prerelease": incluir_prerelease,
        "releases": todas,
        "comparacoes": comparacoes,
        "ignoradas_404": ignoradas_404,
    }


def salvar_releases_json(resultado: dict, caminho: str | Path) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")


def _main() -> None:
    from metricas.lead_time import lead_time_repo

    ap = argparse.ArgumentParser(description="Coleta releases e commits entre releases de um repositório.")
    ap.add_argument("repo", help="owner/nome, ex.: psf/requests")
    ap.add_argument("--inicio", required=True, type=date.fromisoformat)
    ap.add_argument("--fim", required=True, type=date.fromisoformat)
    ap.add_argument("--prerelease", action="store_true", help="conta pré-releases como deploy (variante da RQ 07)")
    ap.add_argument("--saida", default=None, help="JSON de saída (padrão: dados/releases/<owner>__<repo>.json)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    owner, nome = args.repo.split("/", 1)
    gh = GitHubClient()
    resultado = coletar_releases(gh, owner, nome, args.inicio, args.fim, args.prerelease)

    saida = args.saida or f"dados/releases/{owner}__{nome}.json"
    salvar_releases_json(resultado, saida)

    print(f"{args.repo}: {len(resultado['comparacoes'])} releases na janela -> {saida}")
    print(f"  ignoradas por 404: {resultado['ignoradas_404']}")
    print(f"  lead time: {lead_time_repo(resultado['comparacoes'])}")
    print(f"  chamadas à API: {gh.chamadas_api} | do cache: {gh.acertos_cache}")


if __name__ == "__main__":
    _main()
