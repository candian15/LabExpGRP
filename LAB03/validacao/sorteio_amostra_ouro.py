"""Sorteio da amostra-ouro (seção 6, passo 1).

- 60 repositórios da amostra final com ``df.sample(n=60, random_state=42)``;
- 5 releases por repositório, também com semente 42, entre as que têm release
  anterior e ``compare`` sem erro (sem a lista de commits não dá para julgar se
  a release é corretiva).

Uso (depois do ``dados/repositorios.csv`` do João; as releases vêm do cache)::

    python -m validacao.sorteio_amostra_ouro
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.__main__ import carregar_config
from pipeline.coleta_releases import coletar_releases
from pipeline.github_client import GitHubClient
from validacao.comum import PASTA, SEMENTE, escrever_csv


def main() -> None:
    cfg = carregar_config("config.yaml")
    df = pd.read_csv(Path(cfg["saida"]) / "repositorios.csv", dtype=str, keep_default_na=False)
    aprovados = df[df["motivo_descarte"] == ""].sort_values("repo")  # ordena: sorteio não depende da ordem do CSV
    repos = sorted(aprovados.sample(n=60, random_state=SEMENTE)["repo"])

    gh = GitHubClient(cache_dir=cfg["cache"])
    releases = []
    for repo in repos:
        owner, nome = repo.split("/", 1)
        comparacoes = coletar_releases(gh, owner, nome, cfg["inicio"], cfg["fim"])["comparacoes"]
        validas = pd.DataFrame([c for c in comparacoes if c["status"] == "ok"])
        if validas.empty:
            continue
        escolhidas = validas.sort_values("published_at").sample(n=min(5, len(validas)), random_state=SEMENTE)
        for c in escolhidas.sort_values("published_at").to_dict("records"):
            releases.append({
                "repo": repo,
                "tag": c["tag_name"],
                "link": c.get("html_url") or f"https://github.com/{repo}/releases/tag/{c['tag_name']}",
                "link_commits": f"https://github.com/{repo}/compare/{c['anterior']}...{c['tag_name']}",
            })

    escrever_csv([{"repo": r} for r in repos], ["repo"], PASTA / "amostra_ouro_repos.csv")
    escrever_csv(releases, ["repo", "tag", "link", "link_commits"], PASTA / "amostra_ouro_releases.csv")
    print(f"{len(repos)} repositórios e {len(releases)} releases sorteados (semente {SEMENTE}).")


if __name__ == "__main__":
    main()
