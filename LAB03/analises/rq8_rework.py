"""RQ 08 (bônus): deployment rework rate.

Rework rate = releases corretivas ÷ total de releases da janela, usando a mesma
heurística de release corretiva do CFR (b). A diferença para o CFR (b):

- rework rate conta a própria release corretiva (o "conserto");
- CFR (b) conta a release que *precisou* de conserto em até 7 dias.

Uso (a partir da pasta LAB03)::

    python -m analises.rq8_rework
"""

from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from analises.utils import carregar_repositorios


def resumo(serie: pd.Series) -> dict:
    s = serie.dropna()
    return {
        "n": len(s),
        "mediana": round(s.median(), 4),
        "q1": round(s.quantile(0.25), 4),
        "q3": round(s.quantile(0.75), 4),
    }


def main() -> None:
    df = carregar_repositorios("dados/repositorios.csv")
    df["rework_rate"] = df["cfrb_releases_corretivas"] / df["n_releases"]

    tabela = pd.DataFrame([
        {"metrica": "rework_rate", **resumo(df["rework_rate"])},
        {"metrica": "cfr_entrega", **resumo(df["cfr_entrega"])},
    ])
    ambos = df.dropna(subset=["rework_rate", "cfr_entrega"])
    rho, p = spearmanr(ambos["rework_rate"], ambos["cfr_entrega"])
    maior = int((ambos["rework_rate"] > ambos["cfr_entrega"]).sum())
    zero = int((df["rework_rate"] == 0).sum())

    Path("resultados").mkdir(exist_ok=True)
    tabela.to_csv("resultados/rq8_rework.csv", index=False)
    df[["repo", "n_releases", "cfrb_releases_corretivas", "rework_rate", "cfr_entrega"]].to_csv(
        "resultados/rq8_rework_por_repo.csv", index=False)

    print(f"Heurística: {df['cfrb_heuristica'].iloc[0]} | repositórios: {len(df)}\n")
    print(tabela.to_string(index=False))
    print(f"\nSpearman rework × CFR (b): ρ = {rho:.3f}, p = {p:.3g}, n = {len(ambos)}")
    print(f"Repositórios com rework rate > CFR (b): {maior} de {len(ambos)}")
    print(f"Repositórios sem nenhuma release corretiva: {zero}")


if __name__ == "__main__":
    main()
