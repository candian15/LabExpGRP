"""RQ 01 a RQ 04: estatística descritiva das quatro métricas DORA.

Para cada métrica, mediana e IQR (o enunciado pede mediana e IQR, não média e
desvio, porque as distribuições são assimétricas e têm cauda longa), e a
distribuição das categorias Elite/High/Medium/Low.

O tempo de recuperação (RQ 04) tem um detalhe: os repositórios sem nenhum
episódio de falha seguida de sucesso na janela não têm o que medir. Eles ficam
fora da mediana e são listados à parte, como o enunciado pede. Dos que têm
episódio, reportamos também a mediana da proporção de episódios censurados
(episódios que a janela não viu fechar).

Uso (a partir de LAB03/):

    python -m analises.rq1_rq4_descritiva --csv dados/repositorios.csv --saida resultados
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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

COL_EPISODIOS = "n_episodios"
COL_CENSURADOS = "prop_censurados"
COL_DORA = "dora"

# A ordem é a do melhor para o pior, e não a alfabética, para as tabelas e o gráfico.
CATEGORIAS = ["Elite", "High", "Medium", "Low"]

# métrica -> (RQ, rótulo, unidade, escala logarítmica no gráfico)
# Log em frequência, lead time e recuperação: variam em ordens de grandeza.
# O CFR é uma fração entre 0 e 1 e tem zeros, então fica em escala linear.
ESCALA_LOG = True


def metricas(col_cfr_b: str) -> list[dict]:
    return [
        {"rq": "RQ01", "metrica": "deployment_frequency", "coluna": COL_FREQUENCIA,
         "rotulo": "Frequência de deploy", "unidade": "releases/semana", "log": ESCALA_LOG},
        {"rq": "RQ02", "metrica": "lead_time_a", "coluna": COL_LEAD_A,
         "rotulo": "Lead time (a)", "unidade": "horas", "log": ESCALA_LOG},
        {"rq": "RQ02", "metrica": "lead_time_b", "coluna": COL_LEAD_B,
         "rotulo": "Lead time (b)", "unidade": "horas", "log": ESCALA_LOG},
        {"rq": "RQ03", "metrica": "cfr_a_ci", "coluna": COL_CFR_A,
         "rotulo": "CFR (a), proxy de CI", "unidade": "fração", "log": False},
        {"rq": "RQ03", "metrica": "cfr_b_entrega", "coluna": col_cfr_b,
         "rotulo": "CFR (b), proxy de entrega", "unidade": "fração", "log": False},
        {"rq": "RQ04", "metrica": "recuperacao", "coluna": COL_RECUPERACAO,
         "rotulo": "Tempo de recuperação", "unidade": "horas", "log": ESCALA_LOG},
    ]


def resumo(serie: pd.Series) -> dict:
    """Q1, mediana, Q3, IQR e n de uma série, ignorando os valores ausentes."""
    s = serie.dropna()
    if s.empty:
        return {"n": 0, "q1": float("nan"), "mediana": float("nan"),
                "q3": float("nan"), "iqr": float("nan"), "minimo": float("nan"),
                "maximo": float("nan")}
    q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
    return {"n": int(s.size), "q1": q1, "mediana": float(s.median()), "q3": q3,
            "iqr": q3 - q1, "minimo": float(s.min()), "maximo": float(s.max())}


def tabela_descritiva(df: pd.DataFrame, defs: list[dict]) -> pd.DataFrame:
    """Uma linha por métrica, mais a proporção de episódios censurados da RQ 04."""
    linhas = []
    for d in defs:
        linhas.append({"rq": d["rq"], "metrica": d["metrica"], "rotulo": d["rotulo"],
                       "unidade": d["unidade"], **resumo(df[d["coluna"]])})
    if COL_CENSURADOS in df.columns and COL_EPISODIOS in df.columns:
        com_episodio = df.loc[df[COL_EPISODIOS] > 0, COL_CENSURADOS]
        linhas.append({"rq": "RQ04", "metrica": "prop_censurados",
                       "rotulo": "Episódios censurados (só quem tem episódio)",
                       "unidade": "fração", **resumo(com_episodio)})
    cols = ["rq", "metrica", "rotulo", "unidade", "n", "minimo", "q1", "mediana", "q3", "iqr", "maximo"]
    return pd.DataFrame(linhas)[cols]


def distribuicao_dora(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem e porcentagem de cada categoria, na ordem Elite -> Low."""
    contagem = df[COL_DORA].value_counts()
    total = int(contagem.sum())
    linhas = [{"categoria": c, "n": int(contagem.get(c, 0)),
               "pct": round(100 * int(contagem.get(c, 0)) / total, 2) if total else 0.0}
              for c in CATEGORIAS]
    extras = sorted(set(contagem.index) - set(CATEGORIAS))
    linhas += [{"categoria": c, "n": int(contagem[c]), "pct": round(100 * int(contagem[c]) / total, 2)}
               for c in extras]
    return pd.DataFrame(linhas)


def distribuicao_notas(df: pd.DataFrame) -> pd.DataFrame:
    """Distribuição das notas 1 a 4 em cada métrica que entra na classificação."""
    notas = {"nota_frequencia": "RQ01", "nota_lead_time": "RQ02",
             "nota_cfr": "RQ03", "nota_recuperacao": "RQ04"}
    linhas = []
    for col, rq in notas.items():
        if col not in df.columns:
            continue
        contagem = df[col].value_counts()
        total = int(contagem.sum())
        for nota, nome in zip((4, 3, 2, 1), CATEGORIAS):
            n = int(contagem.get(nota, 0))
            linhas.append({"rq": rq, "nota_de": col, "nota": nota, "categoria": nome, "n": n,
                           "pct": round(100 * n / total, 2) if total else 0.0})
    return pd.DataFrame(linhas)


def sem_recuperacao(df: pd.DataFrame) -> pd.DataFrame:
    """Repositórios sem episódio de recuperação na janela, que ficam fora da RQ 04."""
    if COL_EPISODIOS not in df.columns:
        return pd.DataFrame(columns=["repo", "n_episodios", "n_runs_validos", "cfr_ci", "dora"])
    fora = df[df[COL_EPISODIOS] == 0]
    cols = [c for c in ("repo", COL_EPISODIOS, "n_runs_validos", COL_CFR_A, COL_DORA) if c in df.columns]
    return fora[cols].sort_values("repo").reset_index(drop=True)


def grafico_distribuicoes(df: pd.DataFrame, defs: list[dict], caminho: str | Path) -> None:
    """Um histograma por métrica, com escala log onde a variação é de ordens de grandeza."""
    fig, eixos = plt.subplots(2, 3, figsize=(14, 7.5))
    for ax, d in zip(eixos.ravel(), defs):
        s = df[d["coluna"]].dropna()
        if d["log"]:
            s = s[s > 0]  # a escala log não aceita zero nem negativo
            ax.set_xscale("log")
            # Bins em progressão geométrica: com eixo log e bins lineares, quase
            # tudo cairia na primeira barra e o gráfico não mostraria nada.
            bins = np.logspace(np.log10(s.min()), np.log10(s.max()), 31)
        else:
            bins = 30
        ax.hist(s, bins=bins, color="#4a7ebb", edgecolor="white", linewidth=0.4)
        ax.axvline(s.median(), color="#c0392b", linestyle="--", linewidth=1.2,
                   label=f"mediana = {s.median():.4g}")
        ax.set_title(f"{d['rq']}: {d['rotulo']}", fontsize=10)
        ax.set_xlabel(d["unidade"] + (" (escala log)" if d["log"] else ""), fontsize=9)
        ax.set_ylabel("repositórios", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    _salvar(fig, caminho)


def grafico_pares(df: pd.DataFrame, col_cfr_b: str, caminho: str | Path) -> None:
    """As duas variantes lado a lado: lead time (a) x (b) e CFR (a) x (b)."""
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.5))
    pares = [
        (eixos[0], [COL_LEAD_A, COL_LEAD_B], ["(a) commit mais antigo", "(b) todos os commits"],
         "Lead time (horas, escala log)", True),
        (eixos[1], [COL_CFR_A, col_cfr_b], ["(a) proxy de CI", "(b) proxy de entrega"],
         "Change failure rate (fração)", False),
    ]
    for ax, cols, nomes, titulo, log in pares:
        dados = [df[c].dropna() for c in cols]
        if log:
            dados = [s[s > 0] for s in dados]
            ax.set_yscale("log")
        ax.boxplot(dados, tick_labels=nomes, showfliers=False)
        for i, s in enumerate(dados, 1):
            ax.annotate(f"mediana\n{s.median():.4g}", (i, s.median()), textcoords="offset points",
                        xytext=(28, -6), fontsize=8, color="#c0392b")
        ax.set_ylabel(titulo, fontsize=9)
        ax.grid(alpha=0.3, axis="y")
    eixos[0].set_title("RQ 02: lead time nas duas variantes", fontsize=10)
    eixos[1].set_title("RQ 03: CFR nas duas variantes", fontsize=10)
    fig.tight_layout()
    _salvar(fig, caminho)


def grafico_dora(dist: pd.DataFrame, caminho: str | Path) -> None:
    """Barras da classificação DORA geral."""
    cores = {"Elite": "#2e7d32", "High": "#7cb342", "Medium": "#f9a825", "Low": "#c62828"}
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    barras = ax.bar(dist["categoria"], dist["n"],
                    color=[cores.get(c, "#90a4ae") for c in dist["categoria"]])
    for b, n, pct in zip(barras, dist["n"], dist["pct"]):
        ax.annotate(f"{n}\n({pct:.1f}%)", (b.get_x() + b.get_width() / 2, n),
                    ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("repositórios", fontsize=9)
    ax.set_title("Classificação DORA geral (mediana das quatro notas)", fontsize=10)
    ax.set_ylim(0, dist["n"].max() * 1.18)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    _salvar(fig, caminho)


def _salvar(fig, caminho: str | Path) -> None:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m analises.rq1_rq4_descritiva",
                                 description=__doc__.split("\n")[0])
    ap.add_argument("--csv", default="dados/repositorios.csv")
    ap.add_argument("--saida", default="resultados")
    ap.add_argument("--col-cfr-b", default=None, help="nome da coluna do CFR (b) no CSV")
    args = ap.parse_args(argv)

    df = carregar_repositorios(args.csv)
    col_b = achar_coluna(df, CANDIDATAS_CFR_B, args.col_cfr_b)
    defs = metricas(col_b)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    descritiva = tabela_descritiva(df, defs)
    dist = distribuicao_dora(df)
    notas = distribuicao_notas(df)
    fora = sem_recuperacao(df)

    descritiva.to_csv(saida / "rq1_rq4_descritiva.csv", index=False)
    dist.to_csv(saida / "rq1_rq4_dora.csv", index=False)
    notas.to_csv(saida / "rq1_rq4_notas.csv", index=False)
    fora.to_csv(saida / "rq1_rq4_sem_recuperacao.csv", index=False)

    grafico_distribuicoes(df, defs, saida / "rq1_rq4_distribuicoes.png")
    grafico_pares(df, col_b, saida / "rq1_rq4_pares.png")
    grafico_dora(dist, saida / "rq1_rq4_dora.png")

    print(f"{len(df)} repositórios aprovados.\n")
    print(descritiva.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print("\nClassificação DORA geral:")
    print(dist.to_string(index=False))
    if not fora.empty:
        print(f"\n{len(fora)} repositórios sem episódio de recuperação na janela: "
              f"ficam fora da mediana da RQ 04 e estão em rq1_rq4_sem_recuperacao.csv.")
    print(f"\nEscrito em {saida}/: 4 CSVs e 3 gráficos.")


if __name__ == "__main__":
    main()
