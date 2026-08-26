"""
Análise de consistência RQ01 + RQ02 — Lab01S02

Lê o CSV gerado por rq01_rq02_extract.py --full e reporta:
- valores ausentes
- estatísticas de distribuição (média, mediana, desvio padrão, min, max)
- outliers (método IQR - intervalo interquartil)

Uso:
    python analyze_rq01_rq02.py rq01_rq02_1000.csv
"""

import sys
import csv
import statistics


def load_data(filename):
    rows = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def check_missing(rows, field):
    missing = 0
    for r in rows:
        val = r.get(field, "")
        if val is None or val == "" or val == "None" or "ERRO" in str(val):
            missing += 1
    return missing


def to_numeric(rows, field):
    values = []
    for r in rows:
        val = r.get(field, "")
        try:
            values.append(float(val))
        except (ValueError, TypeError):
            continue
    return values


def detect_outliers_iqr(values):
    if len(values) < 4:
        return [], None, None
    sorted_vals = sorted(values)
    q1 = statistics.quantiles(sorted_vals, n=4)[0]
    q3 = statistics.quantiles(sorted_vals, n=4)[2]
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = [v for v in values if v < lower or v > upper]
    return outliers, lower, upper


def print_stats(name, values):
    print(f"\n--- {name} ---")
    if not values:
        print("Nenhum valor numérico encontrado.")
        return
    print(f"n = {len(values)}")
    print(f"média   = {statistics.mean(values):.2f}")
    print(f"mediana = {statistics.median(values):.2f}")
    print(f"desvio padrão = {statistics.pstdev(values):.2f}")
    print(f"min = {min(values):.2f} | max = {max(values):.2f}")

    outliers, lower, upper = detect_outliers_iqr(values)
    if lower is not None:
        print(f"limites IQR: [{lower:.2f}, {upper:.2f}]")
        print(f"outliers detectados: {len(outliers)} ({len(outliers)/len(values)*100:.1f}% da amostra)")
        if outliers:
            print(f"exemplos de outliers: {sorted(outliers, reverse=True)[:5]}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_rq01_rq02.py <arquivo.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    rows = load_data(filename)
    print(f"Total de linhas carregadas: {len(rows)}")

    for field in ["age_years", "merged_prs", "created_at", "stars"]:
        missing = check_missing(rows, field)
        pct = (missing / len(rows) * 100) if rows else 0
        print(f"Valores ausentes/erro em '{field}': {missing} ({pct:.1f}%)")

    age_values = to_numeric(rows, "age_years")
    prs_values = to_numeric(rows, "merged_prs")

    print_stats("RQ01 - Idade do repositório (anos)", age_values)
    print_stats("RQ02 - PRs mergeadas (contribuição externa)", prs_values)


if __name__ == "__main__":
    main()
