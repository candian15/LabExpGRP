"""
RQ07 - Análise cruzada por linguagem - Lab01S03

RQ07: "Sistemas escritos em linguagens mais populares recebem mais contribuição
externa, lançam mais releases e são atualizados com mais frequência?"
=> divide os resultados das RQ02, RQ03 e RQ04 por linguagem primária (RQ05).

Este script NÃO consulta a API. Ele apenas junta (merge) os CSVs já gerados
pelas outras partes do grupo, usando a coluna `repo` como chave, e agrega as
métricas por linguagem.

Entradas esperadas (CSVs de 1000 repositórios, gerados com --full):
  - rq01_rq02_1000.csv   -> colunas: repo, ..., merged_prs            (RQ02)
  - rq03_rq04_1000.csv   -> colunas: repo, ..., total_releases,
                                      days_since_update               (RQ03, RQ04)
  - rq05_rq06_1000.csv   -> colunas: repo, ..., primary_language      (RQ05)

Saída:
  - rq07_por_linguagem.csv  -> uma linha por linguagem, com as medianas das
                               métricas e a contagem de repositórios.

Uso:
    python rq07_analysis.py \\
        --rq02 rq01_rq02_1000.csv \\
        --rq0304 rq03_rq04_1000.csv \\
        --rq05 rq05_rq06_1000.csv
"""

import sys
import csv
import argparse
import statistics
from collections import defaultdict


def load_csv(filename):
    """Carrega um CSV como lista de dicts, indexado por `repo`."""
    by_repo = {}
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            repo = row.get("repo")
            if repo:
                by_repo[repo] = row
    return by_repo


def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def merge_datasets(rq02, rq0304, rq05):
    """
    Junta os três datasets pela chave `repo`. Um repositório só entra na análise
    se estiver presente nos três arquivos (inner join), garantindo que todas as
    métricas existam para cada linha.
    """
    merged = []
    faltando = 0
    for repo, r05 in rq05.items():
        r02 = rq02.get(repo)
        r34 = rq0304.get(repo)
        if r02 is None or r34 is None:
            faltando += 1
            continue
        merged.append(
            {
                "repo": repo,
                "primary_language": r05.get("primary_language", "N/A") or "N/A",
                "merged_prs": to_float(r02.get("merged_prs")),
                "total_releases": to_float(r34.get("total_releases")),
                "days_since_update": to_float(r34.get("days_since_update")),
            }
        )
    return merged, faltando


def median_or_none(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return statistics.median(vals)


def aggregate_by_language(merged):
    """Agrupa por linguagem e calcula a mediana de cada métrica."""
    groups = defaultdict(lambda: {"prs": [], "releases": [], "days": []})
    for row in merged:
        lang = row["primary_language"]
        groups[lang]["prs"].append(row["merged_prs"])
        groups[lang]["releases"].append(row["total_releases"])
        groups[lang]["days"].append(row["days_since_update"])

    resultado = []
    for lang, m in groups.items():
        n = len(m["prs"])
        resultado.append(
            {
                "linguagem": lang,
                "qtd_repos": n,
                "mediana_prs_aceitas": median_or_none(m["prs"]),        # RQ02
                "mediana_releases": median_or_none(m["releases"]),      # RQ03
                "mediana_dias_sem_update": median_or_none(m["days"]),   # RQ04
            }
        )
    # ordena por quantidade de repositórios (linguagem mais frequente primeiro)
    resultado.sort(key=lambda x: x["qtd_repos"], reverse=True)
    return resultado


def save_csv(resultado, filename):
    fieldnames = [
        "linguagem",
        "qtd_repos",
        "mediana_prs_aceitas",
        "mediana_releases",
        "mediana_dias_sem_update",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultado)
    print(f"\nSalvo em: {filename}")


def print_table(resultado, top=None):
    print("\n--- RQ07: métricas medianas por linguagem ---")
    header = f"{'linguagem':<18}{'repos':>7}{'PRs (med)':>12}{'releases(med)':>15}{'dias s/upd(med)':>17}"
    print(header)
    print("-" * len(header))
    rows = resultado if top is None else resultado[:top]
    for r in rows:
        prs = f"{r['mediana_prs_aceitas']:.1f}" if r["mediana_prs_aceitas"] is not None else "N/A"
        rel = f"{r['mediana_releases']:.1f}" if r["mediana_releases"] is not None else "N/A"
        days = f"{r['mediana_dias_sem_update']:.1f}" if r["mediana_dias_sem_update"] is not None else "N/A"
        print(f"{r['linguagem']:<18}{r['qtd_repos']:>7}{prs:>12}{rel:>15}{days:>17}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq02", required=True, help="CSV com merged_prs (rq01_rq02_1000.csv)")
    parser.add_argument("--rq0304", required=True, help="CSV com total_releases e days_since_update (rq03_rq04_1000.csv)")
    parser.add_argument("--rq05", required=True, help="CSV com primary_language (rq05_rq06_1000.csv)")
    parser.add_argument("--out", default="rq07_por_linguagem.csv", help="CSV de saída")
    parser.add_argument("--top", type=int, default=15, help="Quantas linguagens mostrar na tabela")
    args = parser.parse_args()

    rq02 = load_csv(args.rq02)
    rq0304 = load_csv(args.rq0304)
    rq05 = load_csv(args.rq05)
    print(f"Carregados: RQ02={len(rq02)} | RQ03+04={len(rq0304)} | RQ05={len(rq05)} repositórios")

    merged, faltando = merge_datasets(rq02, rq0304, rq05)
    print(f"Repositórios com dados completos (nos 3 arquivos): {len(merged)}")
    if faltando:
        print(f"Ignorados por não constarem nos 3 arquivos: {faltando}")

    resultado = aggregate_by_language(merged)
    print_table(resultado, top=args.top)
    save_csv(resultado, args.out)

    # nota de leitura para o relatório
    print(
        "\nInterpretação: PRs e releases maiores => mais contribuição/atividade; "
        "dias sem update menores => atualização mais frequente."
    )


if __name__ == "__main__":
    main()
