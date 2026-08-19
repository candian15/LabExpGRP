"""
Análise de consistência RQ05 + RQ06 — Lab01S02

Lê o CSV gerado por rq05_rq06_extract.py --full e reporta:
- valores ausentes
- RQ05 (categórica): contagem por linguagem primária
- RQ06 (numérica): distribuição (média, mediana, desvio) e outliers (IQR)

Uso:
    python analyze_rq05_rq06.py rq05_rq06_1000.csv
"""

import sys
import csv
import statistics
from collections import Counter


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
        if val is None or val == "" or val == "None" or val == "N/A" or "ERRO" in str(val):
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
    print(f"média   = {statistics.mean(values):.4f}")
    print(f"mediana = {statistics.median(values):.4f}")
    print(f"desvio padrão = {statistics.pstdev(values):.4f}")
    print(f"min = {min(values):.4f} | max = {max(values):.4f}")

    outliers, lower, upper = detect_outliers_iqr(values)
    if lower is not None:
        print(f"limites IQR: [{lower:.4f}, {upper:.4f}]")
        print(f"outliers detectados: {len(outliers)} ({len(outliers)/len(values)*100:.1f}% da amostra)")
        if outliers:
            print(f"exemplos de outliers: {sorted(outliers, reverse=True)[:5]}")


def print_language_counts(rows):
    """RQ05: contagem por linguagem primária (categórica)."""
    print("\n--- RQ05 - Linguagem primária (contagem) ---")
    langs = [r.get("primary_language", "N/A") or "N/A" for r in rows]
    counter = Counter(langs)
    total = len(langs)
    for lang, count in counter.most_common():
        print(f"{lang:<20} {count:>4} ({count/total*100:.1f}%)")
    print(f"\nlinguagens distintas: {len(counter)}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_rq05_rq06.py <arquivo.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    rows = load_data(filename)
    print(f"Total de linhas carregadas: {len(rows)}")

    for field in ["primary_language", "closed_issue_ratio", "total_issues", "stars"]:
        missing = check_missing(rows, field)
        pct = (missing / len(rows) * 100) if rows else 0
        print(f"Valores ausentes/N/A em '{field}': {missing} ({pct:.1f}%)")

    # RQ05 - categórica
    print_language_counts(rows)

    # RQ06 - numérica
    ratio_values = to_numeric(rows, "closed_issue_ratio")
    print_stats("RQ06 - Razão de issues fechadas (closed/total)", ratio_values)


if __name__ == "__main__":
    main()
