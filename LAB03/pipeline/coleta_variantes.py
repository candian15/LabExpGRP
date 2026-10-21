"""Coleta das variantes de "deploy" para a análise de sensibilidade (RQ 07).

Para cada repositório da amostra final:

- **C2 (release + pré-release):** releases e pré-releases da janela, com os
  commits entre unidades consecutivas. Calcula frequência, lead time (b) e CFR (b).
- **C3 (tag):** tags da janela. Tags não têm data, então usamos a data do commit
  apontado pela tag (``committedDate``). Calcula frequência e lead time (b).

As tags vêm pela API GraphQL: uma consulta traz 100 tags já com a data do
commit, ordenadas da mais nova para a mais antiga, e a busca para quando passa
do início da janela. Os commits entre tags vêm do ``compare`` da REST, como nas
releases. Tudo passa pelo cache, então rodar de novo continua de onde parou.

Uso (a partir da pasta LAB03, com GITHUB_TOKEN definido)::

    python -m pipeline.coleta_variantes

Saída: ``dados/variantes.csv``, lida por ``analises/rq7_sensibilidade.py``.
"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from pathlib import Path

from metricas.cfr_entrega import cfr_entrega
from metricas.frequencia import deployment_frequency
from metricas.lead_time import lead_time_repo
from pipeline.__main__ import carregar_config
from pipeline.coleta_releases import coletar_releases, listar_commits_entre
from pipeline.github_client import ErroGitHub, GitHubClient, NaoEncontrado

log = logging.getLogger(__name__)

CAMPOS = [
    "repo",
    "c2_n_unidades", "c2_frequencia", "c2_lead_time_b_horas", "c2_cfr_entrega",
    "c3_n_tags", "c3_frequencia", "c3_lead_time_b_horas", "c3_tags_404",
]

CONSULTA_TAGS = """
query($owner: String!, $nome: String!, $cursor: String) {
  repository(owner: $owner, name: $nome) {
    refs(refPrefix: "refs/tags/", first: 100, after: $cursor,
         orderBy: {field: TAG_COMMIT_DATE, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        target {
          ... on Commit { committedDate }
          ... on Tag { target { ... on Commit { committedDate } } }
        }
      }
    }
  }
}
"""


def _data_da_tag(no: dict) -> str | None:
    alvo = no.get("target") or {}
    return alvo.get("committedDate") or (alvo.get("target") or {}).get("committedDate")


def listar_tags(gh: GitHubClient, owner: str, nome: str, inicio: date) -> list[dict]:
    """Tags com data, em ordem cronológica, até a primeira anterior à janela.

    A primeira tag antes da janela entra na lista porque é a "anterior" da
    primeira tag da janela (para o compare).
    """
    tags, cursor = [], None
    while True:
        dados = gh.graphql(CONSULTA_TAGS, {"owner": owner, "nome": nome, "cursor": cursor})
        refs = ((dados.get("repository") or {}).get("refs")) or {}
        for no in refs.get("nodes") or []:
            data = _data_da_tag(no)
            if data:  # tags que apontam para árvore/blob não têm data: ficam de fora
                tags.append({"tag_name": no["name"], "published_at": data})
        fim_da_busca = tags and datetime.fromisoformat(tags[-1]["published_at"].replace("Z", "+00:00")).date() < inicio
        if fim_da_busca or not (refs.get("pageInfo") or {}).get("hasNextPage"):
            break
        cursor = refs["pageInfo"]["endCursor"]
    return sorted(tags, key=lambda t: (t["published_at"], t["tag_name"]))


def comparacoes_de_tags(gh: GitHubClient, owner: str, nome: str, tags: list[dict],
                        inicio: date, fim: date) -> list[dict]:
    """Mesmo formato das comparações de releases (serve para ``lead_time_repo``)."""
    comparacoes = []
    for i, t in enumerate(tags):
        if not inicio <= datetime.fromisoformat(t["published_at"].replace("Z", "+00:00")).date() <= fim:
            continue
        item = {**t, "anterior": tags[i - 1]["tag_name"] if i > 0 else None, "status": "ok", "commits": []}
        if item["anterior"] is None:
            item["status"] = "primeira"
        else:
            try:
                item["commits"] = listar_commits_entre(gh, owner, nome, item["anterior"], t["tag_name"])
            except NaoEncontrado:
                item["status"] = "404"
        comparacoes.append(item)
    return comparacoes


def coletar_repo(gh: GitHubClient, repo: str, inicio: date, fim: date, heuristica: str = "v1") -> dict:
    owner, nome = repo.split("/", 1)

    c2 = coletar_releases(gh, owner, nome, inicio, fim, incluir_prerelease=True)["comparacoes"]
    c3 = comparacoes_de_tags(gh, owner, nome, listar_tags(gh, owner, nome, inicio), inicio, fim)

    return {
        "repo": repo,
        "c2_n_unidades": len(c2),
        "c2_frequencia": round(deployment_frequency(len(c2), inicio, fim), 4),
        "c2_lead_time_b_horas": lead_time_repo(c2)["lead_time_b_horas"],
        "c2_cfr_entrega": cfr_entrega(c2, fim, heuristica)["cfr_entrega"] if c2 else None,
        "c3_n_tags": len(c3),
        "c3_frequencia": round(deployment_frequency(len(c3), inicio, fim), 4),
        "c3_lead_time_b_horas": lead_time_repo(c3)["lead_time_b_horas"],
        "c3_tags_404": sum(1 for c in c3 if c["status"] == "404"),
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = carregar_config("config.yaml")
    with open(Path(cfg["saida"]) / "repositorios.csv", encoding="utf-8") as f:
        repos = [l["repo"] for l in csv.DictReader(f) if not (l.get("motivo_descarte") or "").strip()]

    gh = GitHubClient(cache_dir=cfg["cache"])
    print(f"Heurística do CFR (b): {cfg['heuristica_cfrb']} (selecao.heuristica_cfrb no config.yaml)")
    linhas = []
    try:
        for i, repo in enumerate(repos, 1):
            try:
                linhas.append(coletar_repo(gh, repo, cfg["inicio"], cfg["fim"], cfg["heuristica_cfrb"]))
            except ErroGitHub as e:
                log.warning("%s: erro da API, variantes em branco (%s)", repo, e)
                linhas.append({"repo": repo})
            print(f"[{i:>3}/{len(repos)}] {repo}")
    except KeyboardInterrupt:
        print("\nInterrompido. Salvando o que já foi coletado (rodar de novo continua do cache).")

    saida = Path(cfg["saida"]) / "variantes.csv"
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)
    print(f"\n{saida} escrito ({len(linhas)} repositórios).")
    print(f"Chamadas à API: {gh.chamadas_api} | do cache: {gh.acertos_cache}")


if __name__ == "__main__":
    main()