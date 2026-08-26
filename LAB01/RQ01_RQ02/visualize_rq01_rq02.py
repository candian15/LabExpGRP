"""
Visualização RQ01 + RQ02 — Lab01S03

Gera gráficos a partir do CSV coletado em rq01_rq02_1000.csv (Lab01S02):
- RQ01: histograma da idade dos repositórios (anos)
- RQ02: histograma (escala log) do total de PRs mergeadas

Uso:
    python visualize_rq01_rq02.py rq01_rq02_1000.csv
"""

import sys
import csv
import statistics
import matplotlib.pyplot as plt


def load_data(filename):
    ages, prs = [], []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ages.append(float(row["age_years"]))
                prs.append(float(row["merged_prs"]))
            except (ValueError, KeyError):
                continue
    return ages, prs


def plot_rq01(ages, out_path="rq01_idade_histograma.png"):
    median_age = statistics.median(ages)
    mean_age = statistics.mean(ages)

    plt.figure(figsize=(9, 5))
    plt.hist(ages, bins=30, color="#4C72B0", edgecolor="white")
    plt.axvline(median_age, color="#C44E52", linestyle="--",
                label=f"Mediana = {median_age:.1f} anos")
    plt.axvline(mean_age, color="#55A868", linestyle="--",
                label=f"Média = {mean_age:.1f} anos")
    plt.title("RQ01 — Distribuição da idade dos repositórios populares (n=1000)")
    plt.xlabel("Idade (anos)")
    plt.ylabel("Número de repositórios")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")


def plot_rq02(prs, out_path="rq02_prs_histograma.png"):
    median_prs = statistics.median(prs)
    mean_prs = statistics.mean(prs)

    # log(x+1) porque merged_prs tem muitos zeros e distribuição bem assimétrica
    prs_log = [p if p > 0 else 0.5 for p in prs]

    # bins espaçados em escala log, para o histograma ficar legível junto com xscale log
    import math
    min_val = max(min(prs_log), 0.5)
    max_val = max(prs_log)
    bins = [10 ** (math.log10(min_val) + i * (math.log10(max_val) - math.log10(min_val)) / 30)
            for i in range(31)]

    plt.figure(figsize=(9, 5))
    plt.hist(prs_log, bins=bins, color="#DD8452", edgecolor="white")
    plt.xscale("log")
    plt.axvline(median_prs if median_prs > 0 else 0.5, color="#C44E52", linestyle="--",
                label=f"Mediana = {median_prs:.0f} PRs")
    plt.title("RQ02 — Distribuição de PRs mergeadas por repositório (n=1000, escala log)")
    plt.xlabel("Total de PRs mergeadas (escala log)")
    plt.ylabel("Número de repositórios")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")
    print(f"(Média = {mean_prs:.1f} | Mediana = {median_prs:.1f} — a diferença grande")
    print(" confirma a distribuição assimétrica discutida na RQ02)")


def main():
    if len(sys.argv) < 2:
        print("Uso: python visualize_rq01_rq02.py <arquivo.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    ages, prs = load_data(filename)
    print(f"Registros carregados: {len(ages)}")

    plot_rq01(ages)
    plot_rq02(prs)


if __name__ == "__main__":
    main()
