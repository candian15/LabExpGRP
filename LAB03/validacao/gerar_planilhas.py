"""Gera uma planilha de rotulagem por avaliador (seção 6, passo 2).

Para cada repositório sorteado: uma linha ``repositorio`` (tipo do projeto e
entregas reais) seguida das linhas ``release`` (corretiva), com links da release
e dos commits. **A saída da heurística não entra na planilha.**

Uso::

    python -m validacao.gerar_planilhas
"""

from __future__ import annotations

from validacao.comum import AVALIADORES, COLUNAS_PLANILHA, NIVEL_RELEASE, NIVEL_REPO, PASTA, escrever_csv, ler_csv


def main() -> None:
    repos = ler_csv(PASTA / "amostra_ouro_repos.csv")
    releases = ler_csv(PASTA / "amostra_ouro_releases.csv")

    linhas = []
    for r in repos:
        linhas.append({"nivel": NIVEL_REPO, "repo": r["repo"], "link": f"https://github.com/{r['repo']}"})
        linhas += [{"nivel": NIVEL_RELEASE, **rel} for rel in releases if rel["repo"] == r["repo"]]

    for a in AVALIADORES:
        escrever_csv(linhas, COLUNAS_PLANILHA, PASTA / f"rotulos_{a}.csv", delim=";")
        print(f"Planilha gerada: {PASTA / f'rotulos_{a}.csv'}")


if __name__ == "__main__":
    main()
