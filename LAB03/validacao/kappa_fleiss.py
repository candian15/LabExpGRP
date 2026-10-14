"""Kappa de Fleiss entre os três avaliadores (seção 6, passo 3).

Um kappa por dimensão (``aggregate_raters`` + ``fleiss_kappa`` do statsmodels),
interpretado pela escala de Landis & Koch (1977). Itens que algum avaliador
deixou em branco ficam de fora.

Uso::

    python -m validacao.kappa_fleiss
"""

from __future__ import annotations

import numpy as np
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

from validacao.comum import AVALIADORES, DIMENSOES, PASTA, escrever_csv, ler_todos


def interpretar(kappa: float | None) -> str:
    """Escala de Landis & Koch (1977)."""
    if kappa is None:
        return "indefinido"
    if kappa < 0:
        return "pobre"
    if kappa <= 0.20:
        return "leve"
    if kappa <= 0.40:
        return "razoável"
    if kappa <= 0.60:
        return "moderada"
    if kappa <= 0.80:
        return "substancial"
    return "quase perfeita"


def kappa(linhas: list[list[str]]) -> float | None:
    """Kappa de Fleiss de uma matriz itens x avaliadores.

    None se não der para calcular (nenhum item ou todos na mesma categoria).
    """
    categorias = sorted({v for linha in linhas for v in linha})
    if len(categorias) < 2:
        return None
    tabela, _ = aggregate_raters(np.array([[categorias.index(v) for v in linha] for linha in linhas]))
    return float(fleiss_kappa(tabela, method="fleiss"))


def calcular(rotulos: dict) -> list[dict]:
    resultado = []
    for dim in DIMENSOES:
        itens = sorted(set().union(*(rotulos[a][dim] for a in AVALIADORES)))
        linhas = [[rotulos[a][dim].get(i) for a in AVALIADORES] for i in itens]
        completas = [l for l in linhas if None not in l]
        k = kappa(completas)
        resultado.append({
            "dimensao": dim,
            "n_itens": len(completas),
            "n_excluidos": len(linhas) - len(completas),
            "kappa": None if k is None else round(k, 4),
            "interpretacao": interpretar(k),
        })
    return resultado


def main() -> None:
    resultado = calcular(ler_todos())
    escrever_csv(resultado, list(resultado[0]), PASTA / "kappa.csv")
    for r in resultado:
        print(f"{r['dimensao']}: κ = {r['kappa']} ({r['interpretacao']}), "
              f"{r['n_itens']} itens, {r['n_excluidos']} excluídos")


if __name__ == "__main__":
    main()
