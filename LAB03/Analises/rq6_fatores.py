"""RQ 06: que características dos repositórios se associam ao desempenho DORA?

Para cada combinação fator x métrica:

- fator com 3+ grupos: Kruskal-Wallis, com tamanho de efeito ε² = H / (n - 1);
- fator com 2 grupos: Mann-Whitney, com Cliff's delta δ = 2·U1 / (n1·n2) - 1
  (interpretação de Romano et al., 2006: |δ| < 0,147 desprezível; < 0,33 pequeno;
  < 0,474 médio; senão grande).

Os p-valores de **todos** os testes são corrigidos juntos pelo método de Holm
(``statsmodels.stats.multitest.multipletests``).

Fatores: linguagem principal (as mais frequentes; o resto vira "Outras"), e os
quartis de estrelas, de contribuidores e de idade. Se houver um CSV com o tipo do
projeto rotulado (``--tipos``, colunas ``repo`` e ``tipo``), ele entra como quinto fator.

Uso (a partir de LAB03/):

    python -m analises.rq6_fatores --csv dados/repositorios.csv --saida analises/saida
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import kruskal, mannwhitneyu
from statsmodels.stats.multitest import multipletests

from analises.utils import (
    CANDIDATAS_CFR_B,
    COL_CFR_A,
    COL_FREQUENCIA,
    COL_LEAD_A,
    COL_LEAD_B,
    COL_RECUPERACAO,
    achar_coluna,
    carregar_repositorios,
)

ALFA = 0.05
MIN_POR_GRUPO = 5  # grupos menores que isso são descartados do teste
TOP_LINGUAGENS = 5


# ---------------------------------------------------------------- tamanhos de efeito
def epsilon_quadrado(h: float, n: int) -> float:
    """ε² = H / (n - 1) (varia de 0 a 1)."""
    return h / (n - 1) if n > 1 else float("nan")


def cliffs_delta(u1: float, n1: int, n2: int) -> float:
    """δ = 2·U1 / (n1·n2) - 1, com U1 a estatística de ``mannwhitneyu(x, y)``."""
    return 2 * u1 / (n1 * n2) - 1


def interpretar_delta(delta: float) -> str:
    a = abs(delta)
    if a < 0.147:
        return "desprezível"
    if a < 0.33:
        return "pequeno"
    if a < 0.474:
        return "médio"
    return "grande"


# ------------------------------------------------------------------------- fatores
def quartis(serie: pd.Series) -> pd.Series:
    """Quartis Q1..Q4 (menos grupos se houver muitos valores repetidos)."""
    try:
        q = pd.qcut(serie, 4, duplicates="drop")
    except ValueError:
        return pd.Series([pd.NA] * len(serie), index=serie.index, dtype="object")
    rotulos = [f"Q{i + 1}" for i in range(len(q.cat.categories))]
    return q.cat.rename_categories(rotulos).astype("object")


def linguagem_agrupada(serie: pd.Series, top: int = TOP_LINGUAGENS) -> pd.Series:
    """Mantém as ``top`` linguagens mais comuns; o resto vira "Outras"."""
    frequentes = serie.value_counts().head(top).index
    return serie.where(serie.isin(frequentes), "Outras").where(serie.notna())


def montar_fatores(df: pd.DataFrame, tipos: pd.DataFrame | None = None) -> dict[str, pd.Series]:
    fatores: dict[str, pd.Series] = {}
    if "linguagem" in df.columns:
        fatores["linguagem"] = linguagem_agrupada(df["linguagem"])
    for nome, col in (("estrelas", "estrelas"), ("contribuidores", "contribuidores"), ("idade", "idade_anos")):
        if col in df.columns and df[col].notna().sum() >= 8:
            fatores[nome] = quartis(df[col])
    if tipos is not None and "repo" in df.columns:
        tipos = tipos.rename(columns={"tipo_projeto": "tipo"})  # consenso_repos.csv usa tipo_projeto
        tipos = tipos[tipos["tipo"].notna() & (tipos["tipo"].astype(str).str.strip() != "")]
        mapa = tipos.drop_duplicates("repo").set_index("repo")["tipo"]
        fatores["tipo_projeto"] = df["repo"].map(mapa)
    return fatores


# ---------------------------------------------------------------------------- testes
def testar(valores: pd.Series, grupos: pd.Series) -> dict | None:
    """Um teste fator x métrica. Devolve None se não há grupos suficientes."""
    dados = pd.DataFrame({"v": valores, "g": grupos}).dropna()
    contagem = dados["g"].value_counts()
    dados = dados[dados["g"].isin(contagem[contagem >= MIN_POR_GRUPO].index)]
    nomes = sorted(dados["g"].unique())
    if len(nomes) < 2:
        return None
    amostras = [dados.loc[dados["g"] == g, "v"].to_numpy() for g in nomes]
    n = len(dados)
    medianas = {g: float(dados.loc[dados["g"] == g, "v"].median()) for g in nomes}
    base = {
        "n": n,
        "k_grupos": len(nomes),
        "tamanhos": ", ".join(f"{g}={len(a)}" for g, a in zip(nomes, amostras)),
        "medianas": ", ".join(f"{g}={m:.4g}" for g, m in medianas.items()),
    }
    if len(nomes) == 2:
        r = mannwhitneyu(amostras[0], amostras[1])
        delta = cliffs_delta(float(r.statistic), len(amostras[0]), len(amostras[1]))
        return {**base, "teste": "Mann-Whitney", "estatistica": float(r.statistic), "p": float(r.pvalue),
                "efeito_tipo": "Cliff's delta", "efeito": delta, "interpretacao_efeito": interpretar_delta(delta)}
    r = kruskal(*amostras)
    return {**base, "teste": "Kruskal-Wallis", "estatistica": float(r.statistic), "p": float(r.pvalue),
            "efeito_tipo": "epsilon^2", "efeito": epsilon_quadrado(float(r.statistic), n), "interpretacao_efeito": ""}


def rodar(df: pd.DataFrame, metricas: dict[str, str], tipos: pd.DataFrame | None = None) -> pd.DataFrame:
    """Todos os testes fator x métrica, com p-valores corrigidos por Holm em conjunto."""
    linhas = []
    for fator, grupos in montar_fatores(df, tipos).items():
        for nome_metrica, col in metricas.items():
            if col not in df.columns:
                continue
            r = testar(df[col], grupos)
            if r is not None:
                linhas.append({"fator": fator, "metrica": nome_metrica, **r})
    if not linhas:
        return pd.DataFrame()
    out = pd.DataFrame(linhas)
    out["p_holm"] = multipletests(out["p"], method="holm")[1]
    out["significativo_holm"] = out["p_holm"] < ALFA
    ordem = ["fator", "metrica", "teste", "n", "k_grupos", "estatistica", "p", "p_holm", "significativo_holm",
             "efeito_tipo", "efeito", "interpretacao_efeito", "tamanhos", "medianas"]
    return out[ordem]


def metricas_padrao(df: pd.DataFrame, col_cfr_b: str) -> dict[str, str]:
    return {
        "deployment_frequency": COL_FREQUENCIA,
        "lead_time_a": COL_LEAD_A,
        "lead_time_b": COL_LEAD_B,
        "cfr_a_ci": COL_CFR_A,
        "cfr_b_entrega": col_cfr_b,
        "recuperacao": COL_RECUPERACAO,
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m analises.rq6_fatores", description=__doc__.split("\n")[0])
    ap.add_argument("--csv", default="dados/repositorios.csv")
    ap.add_argument("--saida", default="analises/saida")
    ap.add_argument("--col-cfr-b", default=None, help="nome da coluna do CFR (b) no CSV")
    ap.add_argument("--tipos", default=None,
                    help="CSV com repo e tipo/tipo_projeto (ex.: validacao/consenso_repos.csv, gerado pelo consenso)")
    args = ap.parse_args(argv)

    df = carregar_repositorios(args.csv)
    col_b = achar_coluna(df, CANDIDATAS_CFR_B, args.col_cfr_b)
    tipos = pd.read_csv(args.tipos) if args.tipos else None
    resultado = rodar(df, metricas_padrao(df, col_b), tipos)

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(saida / "rq6_testes.csv", index=False)
    print(resultado[["fator", "metrica", "teste", "n", "p", "p_holm", "efeito_tipo", "efeito"]].to_string(index=False))
    sig = int(resultado["significativo_holm"].sum()) if len(resultado) else 0
    print(f"\n{len(resultado)} testes; {sig} significativos após Holm (α = {ALFA}). Escrito em {saida}/rq6_testes.csv")


if __name__ == "__main__":
    main()
