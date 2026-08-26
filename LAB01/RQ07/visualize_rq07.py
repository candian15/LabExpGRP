"""
Visualização RQ07 — Lab01S03

Gera gráficos a partir do CSV agregado por linguagem (rq07_por_linguagem.csv),
que é a saída do rq07_analysis.py. Para cada uma das métricas cruzadas mostra
a mediana por linguagem, considerando apenas as linguagens com uma quantidade
mínima de repositórios (para evitar medianas pouco confiáveis):
- RQ02: mediana de pull requests aceitas por linguagem
- RQ03: mediana de releases por linguagem
- RQ04: mediana de dias sem atualização por linguagem

Uso:
    python visualize_rq07.py rq07_por_linguagem.csv
"""

import sys
import csv
import matplotlib.pyplot as plt

# só considera linguagens com pelo menos este número de repositórios
MIN_REPOS = 10
# quantas linguagens (as com mais repositórios) mostrar em cada gráfico
TOP = 10


def load_data(filename):
    rows = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                qtd = int(row["qtd_repos"])
            except (ValueError, KeyError):
                continue
            if qtd < MIN_REPOS:
                continue
            rows.append(row)
    # já vem ordenado por qtd_repos no CSV, mas garantimos aqui
    rows.sort(key=lambda r: int(r["qtd_repos"]), reverse=True)
    return rows[:TOP]


def _to_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def plot_metric(rows, campo, titulo, ylabel, cor, out_path):
    nomes, valores = [], []
    for r in rows:
        val = _to_float(r.get(campo))
        if val is not None:
            nomes.append(r["linguagem"])
            valores.append(val)

    plt.figure(figsize=(9, 5))
    plt.bar(nomes, valores, color=cor, edgecolor="white")
    plt.title(titulo)
    plt.xlabel("Linguagem primária")
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    for i, v in enumerate(valores):
        plt.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Gráfico salvo: {out_path}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python visualize_rq07.py <rq07_por_linguagem.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    rows = load_data(filename)
    print(f"Linguagens consideradas (>= {MIN_REPOS} repos, top {TOP}): {len(rows)}")

    plot_metric(
        rows, "mediana_prs_aceitas",
        f"RQ07 — Mediana de PRs aceitas por linguagem (top {TOP})",
        "Mediana de PRs aceitas", "#4C72B0",
        "rq07_prs_por_linguagem.png",
    )
    plot_metric(
        rows, "mediana_releases",
        f"RQ07 — Mediana de releases por linguagem (top {TOP})",
        "Mediana de releases", "#DD8452",
        "rq07_releases_por_linguagem.png",
    )
    plot_metric(
        rows, "mediana_dias_sem_update",
        f"RQ07 — Mediana de dias sem atualização por linguagem (top {TOP})",
        "Mediana de dias sem atualização", "#55A868",
        "rq07_update_por_linguagem.png",
    )
    print("\nLembrete de leitura: PRs/releases MAIORES => mais atividade; "
          "dias sem update MENORES => atualização mais frequente.")


if __name__ == "__main__":
    main()
