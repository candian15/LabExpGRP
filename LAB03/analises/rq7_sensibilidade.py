"""RQ 07: o quanto a classificação DORA depende da definição operacional.

Três combinações (tabela do enunciado):

| Combinação      | Unidade de deploy     | Lead time | CFR |
|-----------------|-----------------------|-----------|-----|
| C1 (referência) | release               | (a)       | (a) |
| C2              | release + pré-release | (b)       | (b) |
| C3              | tag                   | (b)       | (a) |

O tempo de recuperação é o mesmo nas três (não depende da unidade de deploy).
Para cada par de combinações: % de repositórios que mudam de categoria e kappa
de Cohen ponderado (``weights="linear"``), porque as categorias são ordenadas.

Uso (a partir da pasta LAB03, depois de ``python -m pipeline.coleta_variantes``)::

    python -m analises.rq7_sensibilidade
"""

from itertools import combinations
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from analises.utils import carregar_repositorios
from metricas.classificacao import NOMES, classificar

# coluna que indica se a variante foi coletada (vazia = erro na coleta: fica fora)
COLETADA = {"C2": "c2_n_unidades", "C3": "c3_n_tags"}

COMBINACOES = {
    "C1": ("deployment_frequency", "lead_time_a_horas", "cfr_ci"),
    "C2": ("c2_frequencia", "c2_lead_time_b_horas", "c2_cfr_entrega"),
    "C3": ("c3_frequencia", "c3_lead_time_b_horas", "cfr_ci"),
}


def _valor(x):
    return None if pd.isna(x) else float(x)


def classificar_combinacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Nota DORA geral (1 a 4) de cada repositório em cada combinação."""
    out = df[["repo"]].copy()
    for nome, (freq, lead, cfr) in COMBINACOES.items():
        out[nome] = [
            classificar(_valor(f), _valor(l), _valor(c), _valor(r))["dora_nota"]
            for f, l, c, r in zip(df[freq], df[lead], df[cfr], df["recuperacao_horas"])
        ]
        if nome in COLETADA:
            out.loc[df[COLETADA[nome]].isna(), nome] = None
    return out


def comparar_pares(notas: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for a, b in combinations(COMBINACOES, 2):
        par = notas[[a, b]].dropna()
        linhas.append({
            "par": f"{a} x {b}",
            "n": len(par),
            "pct_mudou": round(100 * (par[a] != par[b]).mean(), 1),
            "kappa_ponderado": round(cohen_kappa_score(par[a].astype(int), par[b].astype(int), weights="linear"), 3),
        })
    return pd.DataFrame(linhas)


def distribuicao(notas: pd.DataFrame) -> pd.DataFrame:
    tabela = {c: notas[c].map(NOMES).value_counts() for c in COMBINACOES}
    return pd.DataFrame(tabela).reindex(["Elite", "High", "Medium", "Low"]).fillna(0).astype(int)


def main() -> None:
    df = carregar_repositorios("dados/repositorios.csv").merge(
        pd.read_csv("dados/variantes.csv"), on="repo", how="left")
    notas = classificar_combinacoes(df)
    pares = comparar_pares(notas)
    dist = distribuicao(notas)

    Path("resultados").mkdir(exist_ok=True)
    notas.assign(**{c: notas[c].map(NOMES) for c in COMBINACOES}).to_csv("resultados/rq7_classificacoes.csv", index=False)
    pares.to_csv("resultados/rq7_pares.csv", index=False)
    dist.to_csv("resultados/rq7_distribuicao.csv")

    print(f"Repositórios: {len(df)} (sem variantes coletadas: {df['c3_n_tags'].isna().sum()})\n")
    print("Distribuição por combinação:")
    print(dist.to_string())
    print("\nComparação entre pares:")
    print(pares.to_string(index=False))


if __name__ == "__main__":
    main()
