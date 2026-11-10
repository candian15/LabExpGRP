"""Simulação de Monte Carlo das perguntas Q1 (erro tipo I) e Q2 (poder).

Convenção do efeito (a mesma do config/cenario.yaml): o controle usa mu e sigma do grupo
sem bot; o tratamento usa mu + ln(razao) e o mesmo sigma. razao = 1 significa H0 verdadeira.

Uso (a partir de LAB04/):  python -m src.monte_carlo
Grava resultados/q1.csv e resultados/q2.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.simulacao import ler_cenario

N_REP = 10_000
ALFA = 0.05
PASTA_RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"


def taxas_de_amostras(A, B, alfa=ALFA):
    """Recebe duas matrizes (repetições x n) e devolve a proporção de rejeições de cada teste."""
    p_welch = stats.ttest_ind(A, B, axis=1, equal_var=False).pvalue
    p_mw = stats.mannwhitneyu(A, B, axis=1, alternative="two-sided").pvalue
    return {"Welch": float((p_welch < alfa).mean()),
            "Mann-Whitney": float((p_mw < alfa).mean())}


def taxa_rejeicao(mu, sigma, n, razao, rng, n_rep=N_REP):
    """Gera n_rep conjuntos (controle x tratamento) e aplica os dois testes em todos."""
    A = rng.lognormal(mu, sigma, (n_rep, n))
    B = rng.lognormal(mu + np.log(razao), sigma, (n_rep, n))
    return taxas_de_amostras(A, B)


def simular(situacao, mu, sigma, n, razoes, rng, n_rep=N_REP):
    """Roda a simulação para cada razão e devolve uma tabela com uma linha por teste."""
    linhas = []
    for razao in razoes:
        for teste, taxa in taxa_rejeicao(mu, sigma, n, razao, rng, n_rep).items():
            linhas.append({"situacao": situacao, "n": n, "sigma": sigma, "razao": razao,
                           "teste": teste, "taxa_rejeicao": taxa})
    return pd.DataFrame(linhas)


def main():
    cenario = ler_cenario()
    controle = cenario["grupos"][cenario["controle"]]
    mu, sigma, n = controle["mu"], controle["sigma"], cenario["n_por_grupo"]
    rng = np.random.default_rng(cenario["semente"])

    PASTA_RESULTADOS.mkdir(exist_ok=True)
    q1 = simular("real", mu, sigma, n, [1.0], rng)
    q2 = simular("real", mu, sigma, n, cenario["efeitos_razao_medianas"], rng)
    q1.to_csv(PASTA_RESULTADOS / "q1.csv", index=False)
    q2.to_csv(PASTA_RESULTADOS / "q2.csv", index=False)

    print("Q1 (erro tipo I, razao = 1):")
    print(q1.to_string(index=False))
    print("\nQ2 (poder):")
    print(q2.pivot(index="razao", columns="teste", values="taxa_rejeicao").to_string())


if __name__ == "__main__":
    main()
