"""Q3: o que muda quando os dados não "se comportam bem"?

Repete a Q1 (erro tipo I, razão = 1) e a Q2 (poder, razões de 1,0 a 0,2) em três situações
que as promessas do ``docs/cenario.md`` pedem, cada uma violando um pressuposto do t de
Welch (ou tornando o teste mais difícil) de um jeito diferente:

- ``bem_comportada``: sigma pequeno (0,3); os dados ficam quase simétricos e o Welch está
  no território em que foi feito. É a situação de controle: mostra o que muda quando
  **não** há violação.
- ``n_pequeno``: o sigma real (muito assimétrico) com apenas 10 PRs por grupo.
- ``outliers``: base bem comportada (sigma = 0,3) em que 10% dos valores de cada amostra
  são multiplicados por 10 (cada valor tem 10% de chance de ser contaminado). Partir de
  uma base sem assimetria isola o efeito dos outliers; com o sigma real a cauda já é tão
  pesada que a contaminação não se distinguiria.

A convenção do efeito é a do ``config/cenario.yaml`` e a do ``monte_carlo.py``: o controle
usa ``mu`` e ``sigma`` da situação; o tratamento usa ``mu + ln(razao)`` e o mesmo sigma. Em
cada situação o ``mu`` é o do controle real, e só o que a situação muda (sigma, n,
contaminação) difere do cenário real. Quando há contaminação, ela vale para os dois grupos.

Cada situação usa a sua própria sequência de números aleatórios, derivada da semente do
cenário (``default_rng([semente, 3, i])``), então acrescentar uma situação não muda as
outras e rodar duas vezes dá exatamente o mesmo ``resultados/q3.csv``.

Uso (a partir de LAB04/):  python -m src.q3
Grava resultados/q3.csv, com as mesmas colunas de q1.csv e q2.csv.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.monte_carlo import N_REP, PASTA_RESULTADOS, taxa_rejeicao, taxas_de_amostras
from src.simulacao import ler_cenario

SIGMA_BEM_COMPORTADA = 0.3
N_PEQUENO = 10
FRACAO_OUTLIERS = 0.10  # cada valor tem 10% de chance de ser contaminado...
FATOR_OUTLIERS = 10.0  # ...multiplicados por 10

# situacao -> o que muda em relação ao cenário real (None = igual ao cenário real).
# A ordem aqui define o índice da sequência de números aleatórios de cada situação.
SITUACOES = {
    "bem_comportada": {"sigma": SIGMA_BEM_COMPORTADA, "n": None, "fracao_outliers": 0.0},
    "n_pequeno": {"sigma": None, "n": N_PEQUENO, "fracao_outliers": 0.0},
    "outliers": {"sigma": SIGMA_BEM_COMPORTADA, "n": None, "fracao_outliers": FRACAO_OUTLIERS},
}


def contaminar(amostras, fracao, fator, rng):
    """Multiplica por ``fator`` cada valor com probabilidade ``fracao`` (contaminação de Tukey-Huber).

    Cada valor é contaminado de forma independente, então a quantidade de outliers varia
    de amostra para amostra (em média ``fracao * n``, ou seja, 3 em 30). Contaminar sempre
    exatamente o mesmo número de valores nos dois grupos tornaria a diferença entre as
    médias artificialmente estável e deixaria o Welch conservador demais.
    """
    if fracao == 0:
        return amostras
    mascara = rng.random(amostras.shape) < fracao
    return np.where(mascara, amostras * fator, amostras)


def taxa_rejeicao_contaminada(mu, sigma, n, razao, rng, n_rep=N_REP,
                              fracao=FRACAO_OUTLIERS, fator=FATOR_OUTLIERS):
    """Como ``monte_carlo.taxa_rejeicao``, mas com outliers contaminando os dois grupos."""
    A = rng.lognormal(mu, sigma, (n_rep, n))
    B = rng.lognormal(mu + np.log(razao), sigma, (n_rep, n))
    return taxas_de_amostras(contaminar(A, fracao, fator, rng), contaminar(B, fracao, fator, rng))


def simular_situacao(situacao, mu, sigma, n, razoes, rng, n_rep=N_REP, fracao_outliers=0.0):
    """Uma linha por razão e por teste, no mesmo formato de ``monte_carlo.simular``."""
    linhas = []
    for razao in razoes:
        if fracao_outliers:
            taxas = taxa_rejeicao_contaminada(mu, sigma, n, razao, rng, n_rep, fracao_outliers)
        else:
            taxas = taxa_rejeicao(mu, sigma, n, razao, rng, n_rep)
        for teste, taxa in taxas.items():
            linhas.append({"situacao": situacao, "n": n, "sigma": sigma, "razao": razao,
                           "teste": teste, "taxa_rejeicao": taxa})
    return pd.DataFrame(linhas)


def rodar(cenario=None, n_rep=N_REP) -> pd.DataFrame:
    cenario = cenario or ler_cenario()
    controle = cenario["grupos"][cenario["controle"]]
    mu = controle["mu"]
    razoes = cenario["efeitos_razao_medianas"]  # a mesma lista da Q2: 1,0 (erro tipo I) a 0,2
    tabelas = []
    for i, (situacao, p) in enumerate(SITUACOES.items()):
        rng = np.random.default_rng([cenario["semente"], 3, i])
        sigma = controle["sigma"] if p["sigma"] is None else p["sigma"]
        n = cenario["n_por_grupo"] if p["n"] is None else p["n"]
        tabelas.append(simular_situacao(situacao, mu, sigma, n, razoes, rng, n_rep,
                                        p["fracao_outliers"]))
    return pd.concat(tabelas, ignore_index=True)


def main():
    q3 = rodar()
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    q3.to_csv(PASTA_RESULTADOS / "q3.csv", index=False)

    print("Q3, erro tipo I (razao = 1):")
    print(q3[q3["razao"] == 1.0].pivot(index="situacao", columns="teste",
                                        values="taxa_rejeicao").to_string())
    print("\nQ3, poder:")
    print(q3.pivot_table(index=["situacao", "razao"], columns="teste",
                         values="taxa_rejeicao").to_string())


if __name__ == "__main__":
    main()
