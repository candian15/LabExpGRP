"""
Visualização RQ03 + RQ04 — Lab01S03

Gera gráficos a partir do CSV coletado em rq03_rq04_1000.csv (Lab01S02):
- RQ03: histograma (escala log) do total de releases
- RQ04: histograma (escala log) dos dias desde a última atualização (pushed_at)

Uso:
    python visualize_rq03_rq04.py rq03_rq04_1000.csv
"""

import sys
import csv
import math
import statistics
import matplotlib.pyplot as plt


def load_data(filename):
    releases, days = [], []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                releases.append(float(row["total_releases"]))
                days.append(float(row["days_since_update"]))
            except (ValueError, KeyError):
                continue
    return releases, days


def _log_bins(values, n=30):
    # bins espaçados em escala log, para o histograma ficar legível junto com xscale log
    min_val = max(min(values), 0.5)
    max_val = max(values)
    return [10 ** (math.log10(min_val) + i * (math.log10(max_val) - math.log10(min_val)) / n)
            for i in range(n + 1)]


def plot_rq03(releases, out_path="rq03_releases_histograma.png"):
    median_releases = statistics.median(releases)
    mean_releases = statistics.mean(releases)

    # log(x+1) porque total_releases tem muitos zeros e distribuição bem assimétrica
    releases_log = [r if r > 0 else 0.5 for r in releases]
    bins = _log_bins(releases_log)

    plt.figure(figsize=(9, 5))
    plt.hist(releases_log, bins=bins, color="#4C72B0", edgecolor="white")
    plt.xscale("log")
    plt.axvline(median_releases if median_releases > 0 else 0.5, color="#C44E52", linestyle="--",
                label=f"Mediana = {median_releases:.0f} releases")
    plt.title("RQ03 — Distribuição do total de releases por repositório (n=1000, escala log)")
    plt.xlabel("Total de releases (escala log)")
    plt.ylabel("Número de repositórios")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")
    print(f"(Média = {mean_releases:.1f} | Mediana = {median_releases:.1f} — a diferença grande")
    print(" confirma a distribuição assimétrica discutida na RQ03)")


def plot_rq04(days, out_path="rq04_dias_histograma.png"):
    median_days = statistics.median(days)
    mean_days = statistics.mean(days)

    # log(x+1) porque days_since_update tem muitos valores próximos de zero e outliers grandes
    days_log = [d if d > 0 else 0.5 for d in days]
    bins = _log_bins(days_log)

    plt.figure(figsize=(9, 5))
    plt.hist(days_log, bins=bins, color="#DD8452", edgecolor="white")
    plt.xscale("log")
    plt.axvline(median_days if median_days > 0 else 0.5, color="#C44E52", linestyle="--",
                label=f"Mediana = {median_days:.0f} dias")
    plt.title("RQ04 — Distribuição de dias desde a última atualização (n=1000, escala log)")
    plt.xlabel("Dias desde a última atualização (escala log)")
    plt.ylabel("Número de repositórios")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")
    print(f"(Média = {mean_days:.1f} | Mediana = {median_days:.1f} — quanto MENOR, mais")
    print(" frequente é a atualização)")


def main():
    if len(sys.argv) < 2:
        print("Uso: python visualize_rq03_rq04.py <arquivo.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    releases, days = load_data(filename)
    print(f"Registros carregados: {len(releases)}")

    plot_rq03(releases)
    plot_rq04(days)


if __name__ == "__main__":
    main()
