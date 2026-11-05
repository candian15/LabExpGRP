"""G1: dados reais ao lado dos dados simulados (histograma de cada grupo).

Os tempos até o merge são muito assimétricos (valores de minutos a semanas), então o
eixo horizontal está em escala **logarítmica** e as classes têm largura constante em log.
O eixo vertical é a **proporção de PRs** em cada classe, para que a amostra real (n = 30)
e a simulada (maior, para mostrar a forma da distribuição) possam ser comparadas. As
classes cobrem o intervalo dos dados reais com uma margem; valores simulados fora dele
são somados à primeira ou à última classe.

Uso (a partir de LAB04/):  python -m src.graficos_g1     (grava docs/g1_dados_reais_vs_simulados.png)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy import stats

COR_GRUPO = {"sem_bot": "#7f7f7f", "com_bot": "#2ca02c"}  # as cores dos TESTES (Welch/Mann-Whitney) ficam em G2-G4
ROTULO_GRUPO = {"sem_bot": "Sem bot de revisão", "com_bot": "Com bot de revisão"}
N_SIMULADO_G1 = 1000


def carregar_cenario(caminho: str | Path = "config/cenario.yaml") -> dict:
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


def simular_para_g1(cfg: dict, rng: np.random.Generator, n: int = N_SIMULADO_G1) -> pd.DataFrame:
    """Amostra lognormal de cada grupo, com os parâmetros observados nos dados reais."""
    linhas = []
    for grupo, p in cfg["grupos"].items():
        x = rng.lognormal(mean=p["mu"], sigma=p["sigma"], size=n)
        linhas.append(pd.DataFrame({"grupo": grupo, "horas_ate_merge": x}))
    return pd.concat(linhas, ignore_index=True)


def _legenda(x: np.ndarray) -> str:
    return f"n = {len(x)} · mediana = {np.median(x):.1f} h · assimetria = {stats.skew(x, bias=False):.1f}"


def fig_g1(reais: pd.DataFrame, simulados: pd.DataFrame, col_valor: str = "horas_ate_merge"):
    """Figura 2x2: colunas = grupos; linha de cima = dados reais, linha de baixo = simulados."""
    grupos = [g for g in ("sem_bot", "com_bot") if g in set(reais["grupo"])]
    r = reais[col_valor].to_numpy()
    r = r[r > 0]
    lo, hi = np.floor(np.log10(r.min())) - 0.5, np.ceil(np.log10(r.max())) + 0.5
    bins = np.logspace(lo, hi, 20)

    fig, eixos = plt.subplots(2, len(grupos), figsize=(5.2 * len(grupos), 6.4), sharex=True, squeeze=False)
    for j, g in enumerate(grupos):
        for i, (nome_fonte, df) in enumerate((("Dados reais", reais), ("Dados simulados", simulados))):
            x = df.loc[df["grupo"] == g, col_valor].to_numpy()
            ax = eixos[i][j]
            xc = np.clip(x, bins[0], bins[-1])
            ax.hist(xc, bins=bins, weights=np.full(len(xc), 1 / len(xc)), color=COR_GRUPO[g],
                    alpha=0.85 if i == 0 else 0.55, edgecolor="white", linewidth=0.5, label=ROTULO_GRUPO[g])
            ax.axvline(np.median(x), color="black", linestyle="--", linewidth=1.2, label="Mediana")
            ax.set_xscale("log")
            ax.set_title(f"{ROTULO_GRUPO[g]}: {nome_fonte.lower()}", fontsize=11)
            ax.text(0.97, 0.95, _legenda(x), transform=ax.transAxes, ha="right", va="top", fontsize=8.5,
                    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85, "edgecolor": "#cccccc"})
            ax.grid(alpha=0.3)
            ax.legend(loc="center right", fontsize=8.5, frameon=False)
            if j == 0:
                ax.set_ylabel("Proporção de PRs")
            if i == 1:
                ax.set_xlabel("Tempo até o merge (horas, escala log)")
    fig.suptitle("G1. Tempo até o merge de PRs: dados reais × dados simulados (lognormal)", fontsize=13)
    fig.text(0.5, 0.005, "Eixo horizontal em escala log; valores fora do intervalo mostrado entram na primeira ou na última classe.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    return fig


def main(dados: str = "data/dados_reais.csv", cenario: str = "config/cenario.yaml",
         saida: str = "docs/g1_dados_reais_vs_simulados.png") -> None:
    cfg = carregar_cenario(cenario)
    reais = pd.read_csv(dados)
    simulados = simular_para_g1(cfg, np.random.default_rng(cfg["semente"]))
    fig = fig_g1(reais, simulados)
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida, dpi=150)
    plt.close(fig)
    print(f"gravado {saida}")


if __name__ == "__main__":
    main()
