"""Rótulo de consenso da amostra-ouro (seção 6, passo 4).

1. Maioria simples: se pelo menos 2 dos 3 deram o mesmo rótulo, ele vale.
2. Sem maioria: o caso vai para ``validacao/desempate.csv``; os três decidem em
   reunião, escrevem na coluna ``decisao`` e rodam o script de novo.

Saídas: ``consenso.csv`` (repo, tag, corretiva; lido por ``avaliar_heuristica.py``)
e ``consenso_repos.csv`` (tipo do projeto e entregas reais; usado na RQ 06).

Uso::

    python -m validacao.consenso
"""

from __future__ import annotations

from collections import Counter

from validacao.comum import AVALIADORES, DIMENSOES, PASTA, escrever_csv, ler_csv, ler_todos, normalizar

DESEMPATE = PASTA / "desempate.csv"


def votar(votos: list[str | None]) -> str | None:
    """Rótulo com pelo menos 2 votos, ou None se não houver maioria."""
    contagem = Counter(v for v in votos if v is not None)
    if contagem and contagem.most_common(1)[0][1] >= 2:
        return contagem.most_common(1)[0][0]
    return None


def consolidar(rotulos: dict, decisoes: dict) -> tuple[dict, list[dict]]:
    """({dimensão: {item: rótulo}}, linhas sem maioria para o desempate.csv)."""
    consenso = {d: {} for d in DIMENSOES}
    empates = []
    for dim in DIMENSOES:
        for item in sorted(set().union(*(rotulos[a][dim] for a in AVALIADORES))):
            votos = [rotulos[a][dim].get(item) for a in AVALIADORES]
            rotulo = votar(votos)
            if rotulo is None:
                tag = item[1] if len(item) > 1 else ""
                rotulo = decisoes.get((dim, item[0], tag))
                empates.append({"dimensao": dim, "repo": item[0], "tag": tag,
                                **dict(zip(AVALIADORES, votos)), "decisao": rotulo})
            if rotulo is not None:
                consenso[dim][item] = rotulo
    return consenso, empates


def main() -> None:
    decisoes = {}
    if DESEMPATE.exists():
        for l in ler_csv(DESEMPATE):
            decisoes[(l["dimensao"], l["repo"], l["tag"])] = normalizar(l["dimensao"], l["decisao"])

    consenso, empates = consolidar(ler_todos(), decisoes)

    releases = [{"repo": r, "tag": t, "corretiva": v} for (r, t), v in sorted(consenso["corretiva"].items())]
    repos = sorted({i[0] for i in consenso["tipo_projeto"]} | {i[0] for i in consenso["entregas_reais"]})
    linhas_repos = [{"repo": r, "tipo_projeto": consenso["tipo_projeto"].get((r,), ""),
                     "entregas_reais": consenso["entregas_reais"].get((r,), "")} for r in repos]
    escrever_csv(releases, ["repo", "tag", "corretiva"], PASTA / "consenso.csv")
    escrever_csv(linhas_repos, ["repo", "tipo_projeto", "entregas_reais"], PASTA / "consenso_repos.csv")
    print(f"{PASTA / 'consenso.csv'} e {PASTA / 'consenso_repos.csv'} escritos.")

    if empates:
        escrever_csv(empates, ["dimensao", "repo", "tag", *AVALIADORES, "decisao"], DESEMPATE, delim=";")
        pendentes = sum(1 for e in empates if e["decisao"] is None)
        print(f"{len(empates)} caso(s) sem maioria em {DESEMPATE}; {pendentes} ainda sem decisão da reunião.")


if __name__ == "__main__":
    main()
