"""
Visualização RQ05 + RQ06 — Lab01S03

Gera gráficos a partir do CSV coletado em rq05_rq06_1000.csv (Lab01S02):
- RQ05: gráfico de barras com a contagem de repositórios por linguagem primária
        (categórica, por isso barras e não histograma)
- RQ06: histograma da razão de issues fechadas (closed / total)

Uso:
    python visualize_rq05_rq06.py rq05_rq06_1000.csv
"""

import sys
import csv
import statistics
from collections import Counter
import matplotlib.pyplot as plt


def load_data(filename):
    langs, ratios = [], []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # RQ05 - linguagem (inclui os N/A, tratados como categoria própria)
            langs.append(row.get("primary_language", "N/A") or "N/A")
            # RQ06 - razão (ignora N/A, que são repos com total de issues = 0)
            try:
                ratios.append(float(row["closed_issue_ratio"]))
            except (ValueError, KeyError, TypeError):
                continue
    return langs, ratios


def plot_rq05(langs, top=10, out_path="rq05_linguagens_barras.png"):
    counter = Counter(langs)
    mais_comuns = counter.most_common(top)
    nomes = [c[0] for c in mais_comuns]
    valores = [c[1] for c in mais_comuns]

    plt.figure(figsize=(9, 5))
    plt.bar(nomes, valores, color="#4C72B0", edgecolor="white")
    plt.title(f"RQ05 — Linguagens primárias mais comuns (top {top}, n={len(langs)})")
    plt.xlabel("Linguagem primária")
    plt.ylabel("Número de repositórios")
    plt.xticks(rotation=45, ha="right")
    # anota a contagem em cima de cada barra
    for i, v in enumerate(valores):
        plt.text(i, v, str(v), ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")
    print(f"(linguagens distintas no total: {len(counter)})")


def plot_rq06(ratios, out_path="rq06_issues_histograma.png"):
    median_ratio = statistics.median(ratios)
    mean_ratio = statistics.mean(ratios)

    plt.figure(figsize=(9, 5))
    plt.hist(ratios, bins=30, range=(0, 1), color="#DD8452", edgecolor="white")
    plt.axvline(median_ratio, color="#C44E52", linestyle="--",
                label=f"Mediana = {median_ratio:.2f}")
    plt.axvline(mean_ratio, color="#55A868", linestyle="--",
                label=f"Média = {mean_ratio:.2f}")
    plt.title(f"RQ06 — Distribuição da razão de issues fechadas (n={len(ratios)})")
    plt.xlabel("Razão issues fechadas / total")
    plt.ylabel("Número de repositórios")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")
    print(f"(Média = {mean_ratio:.2f} | Mediana = {median_ratio:.2f})")


def main():
    if len(sys.argv) < 2:
        print("Uso: python visualize_rq05_rq06.py <arquivo.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    langs, ratios = load_data(filename)
    print(f"Registros carregados: {len(langs)} (com razão válida: {len(ratios)})")

    plot_rq05(langs)
    plot_rq06(ratios)


if __name__ == "__main__":
    main()
