"""RQ 05: frequência de deploy x taxa de falha (correlação de Spearman).

Calcula ρ, p-valor e n entre ``deployment_frequency`` e o CFR, separadamente para
as variantes (a) (proxy de CI) e (b) (proxy de entrega), e desenha o gráfico de
dispersão com a frequência em escala logarítmica (os valores variam em ordens de
grandeza). Spearman usa os postos, então os muitos CFR iguais a 0 viram empates
tratados pela média dos postos.

Uso (a partir de LAB03/):

    python -m analises.rq5_correlacao --csv dados/repositorios.csv --saida analises/saida
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from analises.utils import CANDIDATAS_CFR_B, COL_CFR_A, COL_FREQUENCIA, achar_coluna, carregar_repositorios

ALFA = 0.05


def interpretar(rho: float) -> str:
    """Rótulo usual para |ρ| (Cohen): <0,1 nula; <0,3 fraca; <0,5 moderada; senão forte."""
    a = abs(rho)
    forca = "desprezível" if a < 0.1 else "fraca" if a < 0.3 else "moderada" if a < 0.5 else "forte"
    sentido = "positiva" if rho > 0 else "negativa" if rho < 0 else ""
    return f"{forca} {sentido}".strip()


def correlacao(df: pd.DataFrame, col_x: str, col_y: str) -> dict:
    """Spearman entre duas colunas, usando só as linhas com os dois valores."""
    par = df[[col_x, col_y]].dropna()
    n = len(par)
    if n < 3 or par[col_x].nunique() < 2 or par[col_y].nunique() < 2:
        return {"n": n, "rho": float("nan"), "p": float("nan"), "interpretacao": "indefinida (poucos dados ou valores constantes)"}
    r = spearmanr(par[col_x], par[col_y])
    return {
        "n": n,
        "rho": float(r.statistic),
        "p": float(r.pvalue),
        "interpretacao": interpretar(float(r.statistic)),
    }


def tabela_spearman(df: pd.DataFrame, col_cfr_b: str) -> pd.DataFrame:
    linhas = []
    for variante, col in (("a (CI)", COL_CFR_A), ("b (entrega)", col_cfr_b)):
        res = correlacao(df, COL_FREQUENCIA, col)
        res.update({"variante_cfr": variante, "coluna_cfr": col, "significativo_5pct": bool(res["p"] < ALFA)})
        linhas.append(res)
    cols = ["variante_cfr", "coluna_cfr", "n", "rho", "p", "significativo_5pct", "interpretacao"]
    return pd.DataFrame(linhas)[cols]


def grafico(df: pd.DataFrame, col_cfr_b: str, tabela: pd.DataFrame, caminho: str | Path) -> None:
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, (variante, col) in zip(eixos, (("a (CI)", COL_CFR_A), ("b (entrega)", col_cfr_b))):
        par = df[[COL_FREQUENCIA, col]].dropna()
        par = par[par[COL_FREQUENCIA] > 0]  # escala log exige > 0
        ax.scatter(par[COL_FREQUENCIA], par[col], s=18, alpha=0.6)
        ax.set_xscale("log")
        ax.set_xlabel("Deployment frequency (releases/semana, escala log)")
        linha = tabela[tabela["variante_cfr"] == variante].iloc[0]
        ax.set_title(f"CFR {variante}: ρ = {linha['rho']:.2f}, p = {linha['p']:.3g}, n = {int(linha['n'])}")
        ax.grid(alpha=0.3)
    eixos[0].set_ylabel("Change failure rate")
    fig.tight_layout()
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m analises.rq5_correlacao", description=__doc__.split("\n")[0])
    ap.add_argument("--csv", default="dados/repositorios.csv")
    ap.add_argument("--saida", default="analises/saida")
    ap.add_argument("--col-cfr-b", default=None, help="nome da coluna do CFR (b) no CSV")
    args = ap.parse_args(argv)

    df = carregar_repositorios(args.csv)
    col_b = achar_coluna(df, CANDIDATAS_CFR_B, args.col_cfr_b)
    tabela = tabela_spearman(df, col_b)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(saida / "rq5_spearman.csv", index=False)
    grafico(df, col_b, tabela, saida / "rq5_dispersao.png")
    print(tabela.to_string(index=False))
    print(f"\nEscrito em {saida}/rq5_spearman.csv e {saida}/rq5_dispersao.png")


if __name__ == "__main__":
    main()
