#!/usr/bin/env python3
"""
dashboard.py - Dashboard consolidado do experimento (S03) - Lab02

Le trials.csv, tests.csv e metrics.csv, junta tudo pela chave
(integrante, kata, tratamento) e gera os graficos que comparam os
tratamentos 'ia' e 'manual':

  rq1_slopegraph.png    DESTAQUE - tempo pareado por kata (manual -> ia)
  rq1_tempo.png         distribuicao do tempo ate o green, por tratamento
  rq2_taxa_sucesso.png  taxa de testes de aceitacao passando, por tratamento
  rq3_metricas.png      complexidade (bruta e por 100 LOC), duplicacao, MI e LOC

Descritivas em mediana + IQR (e nao media + desvio), como pede o enunciado
dado o N pequeno. Novos integrantes entram nos graficos assim que suas
linhas aparecem nos tres CSVs - nao e preciso editar este script.

Uso:
  python dashboard.py
  python dashboard.py --dados . --saida graficos
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

CHAVE = ["integrante", "kata", "tratamento"]
ORDEM = ["ia", "manual"]
CORES = {"ia": "#4C72B0", "manual": "#DD8452"}
TIME_BOX_MIN = 35.0


def carregar(pasta):
    """Junta os tres CSVs em um dataframe com uma linha por trial."""
    def ler(nome):
        df = pd.read_csv(os.path.join(pasta, nome))
        return df.drop(columns=["timestamp"], errors="ignore")

    df = ler("trials.csv").merge(ler("tests.csv"), on=CHAVE).merge(ler("metrics.csv"), on=CHAVE)
    df["tempo_min"] = df["tempo_segundos"] / 60
    # LOC como controle: complexidade crua pode so refletir codigo mais verboso.
    df["complexidade_por100loc"] = df["complexidade_media"] / df["loc"] * 100
    return df.sort_values(CHAVE)


def resumo(df, colunas):
    """Mediana e IQR de cada metrica, por tratamento."""
    agg = df.groupby("tratamento")[colunas].agg(["median", lambda s: s.quantile(.75) - s.quantile(.25)])
    agg.columns = [f"{c}_{'mediana' if f == 'median' else 'iqr'}" for c, f in agg.columns]
    return agg.reindex(ORDEM).dropna(how="all")


def caixa(ax, df, coluna, titulo, rotulo_y):
    """Boxplot por tratamento com os trials individuais sobrepostos."""
    sns.boxplot(df, x="tratamento", y=coluna, order=ORDEM, hue="tratamento",
                palette=CORES, legend=False, width=.5, showfliers=False, ax=ax)
    sns.stripplot(df, x="tratamento", y=coluna, order=ORDEM, color="#222222",
                  size=6, jitter=.12, alpha=.8, ax=ax)
    medianas = df.groupby("tratamento")[coluna].median()
    ax.set_xticks(range(len(ORDEM)),
                  [f"{t}\nmd {medianas.get(t, float('nan')):.1f}" for t in ORDEM])
    if df[coluna].nunique() == 1:
        # metrica constante: sem essa folga, o matplotlib amplia ruido inexistente.
        valor = df[coluna].iloc[0]
        ax.set_ylim(valor - 1, valor + 1)
    ax.set_title(titulo, fontsize=11)
    ax.set_xlabel("")
    ax.set_ylabel(rotulo_y)


def salvar(fig, saida, nome):
    caminho = os.path.join(saida, nome)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    print(f"  {caminho}")


def grafico_slopegraph(df, saida):
    """Grafico-destaque: tempo pareado por kata, manual -> ia.

    Cada kata e um par (within-subject do desenho crossover): a linha desce
    quando a IA foi mais rapida naquele kata e sobe quando foi mais lenta.
    """
    piv = df.pivot_table(index="kata", columns="tratamento", values="tempo_min",
                         aggfunc="median").dropna(subset=ORDEM)
    fig, ax = plt.subplots(figsize=(7, 6))
    for kata, linha in piv.iterrows():
        mais_rapido = linha["ia"] < linha["manual"]
        cor = CORES["ia"] if mais_rapido else "#C44E52"
        ax.plot([0, 1], [linha["manual"], linha["ia"]], marker="o", color=cor, lw=2)
        ax.text(-.06, linha["manual"], f"{kata}  {linha['manual']:.1f}", ha="right",
                va="center", fontsize=9, color=cor)
        ax.text(1.06, linha["ia"], f"{linha['ia']:.1f}", ha="left", va="center",
                fontsize=9, color=cor)

    medianas = [piv["manual"].median(), piv["ia"].median()]
    ax.plot([0, 1], medianas, color="#222222", lw=3, ls="--", marker="s",
            label=f"mediana geral ({medianas[0]:.1f} -> {medianas[1]:.1f} min)")
    ax.set_xlim(-.55, 1.55)
    ax.set_xticks([0, 1], ["manual", "com IA"])
    ax.set_ylabel("Tempo ate passar nos testes (min)")
    ax.set_title(f"RQ1 - Tempo pareado por kata (n={len(piv)} katas)")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    sns.despine(ax=ax, bottom=True)
    salvar(fig, saida, "rq1_slopegraph.png")


def grafico_tempo(df, saida):
    fig, ax = plt.subplots(figsize=(6, 5))
    caixa(ax, df, "tempo_min", f"RQ1 - Tempo ate o green (n={len(df)} trials)",
          "Tempo (min)")
    ax.axhline(TIME_BOX_MIN, color="#C44E52", ls=":", lw=1.5)
    ax.text(1.45, TIME_BOX_MIN, "time-box 35 min", ha="right", va="bottom",
            fontsize=8, color="#C44E52")
    ax.set_ylim(0, TIME_BOX_MIN * 1.08)
    salvar(fig, saida, "rq1_tempo.png")


def grafico_taxa_sucesso(df, saida):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    caixa(axes[0], df, "taxa_sucesso", "Taxa de sucesso dos testes", "% testes passando")
    axes[0].set_ylim(0, 108)
    caixa(axes[1], df, "testes_falhando", "Testes falhando ao final", "nº de testes")
    axes[1].set_ylim(-.5, max(2, df["testes_falhando"].max() + 1))
    fig.suptitle(f"RQ2 - Defeitos por tratamento (n={len(df)} trials)")
    salvar(fig, saida, "rq2_taxa_sucesso.png")


def grafico_metricas(df, saida):
    paineis = [
        ("complexidade_media", "Complexidade ciclomatica media", "McCabe"),
        ("complexidade_por100loc", "Complexidade por 100 LOC", "McCabe / 100 LOC"),
        ("duplicacao_pct", "Duplicacao de codigo", "% linhas duplicadas"),
        ("mi_medio", "Indice de Manutenibilidade", "MI (0-100)"),
        ("loc", "LOC (metrica de controle)", "linhas de codigo"),
    ]
    fig, axes = plt.subplots(1, len(paineis), figsize=(4 * len(paineis), 4.5))
    for ax, (coluna, titulo, rotulo) in zip(axes, paineis):
        caixa(ax, df, coluna, titulo, rotulo)
    fig.suptitle(f"RQ3 - Estrutura do codigo por tratamento (n={len(df)} trials)")
    salvar(fig, saida, "rq3_metricas.png")


def main():
    ap = argparse.ArgumentParser(description="Dashboard consolidado do Lab02 (S03).")
    ap.add_argument("--dados", default=".", help="pasta com trials/tests/metrics.csv")
    ap.add_argument("--saida", default="graficos", help="pasta onde salvar os PNGs")
    args = ap.parse_args()

    df = carregar(args.dados)
    os.makedirs(args.saida, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=.95)

    print(f"{len(df)} trials | integrantes: {', '.join(sorted(df['integrante'].unique()))}"
          f" | katas: {df['kata'].nunique()}")
    if df["censurado"].astype(str).str.lower().eq("true").any():
        print("Atencao: ha trials censurados (atingiram o time-box) - ver trials.csv.")
    if df["taxa_sucesso"].nunique() == 1:
        print("Atencao: taxa de sucesso identica em todos os trials (efeito de teto) -"
              " a RQ2 nao discrimina os tratamentos nesta amostra.")

    colunas = ["tempo_min", "taxa_sucesso", "testes_falhando", "complexidade_media",
               "complexidade_por100loc", "duplicacao_pct", "mi_medio", "loc"]
    tabela = resumo(df, colunas)
    print("\nMediana e IQR por tratamento:")
    print(tabela.T.round(2).to_string())
    tabela.to_csv(os.path.join(args.saida, "resumo_dashboard.csv"))

    print("\nGraficos gerados:")
    grafico_slopegraph(df, args.saida)
    grafico_tempo(df, args.saida)
    grafico_taxa_sucesso(df, args.saida)
    grafico_metricas(df, args.saida)


if __name__ == "__main__":
    main()
