"""Aplica o t de Welch e o Mann-Whitney (bicaudais) a dois grupos, com tamanho do efeito."""
import numpy as np
from scipy import stats

ALFA = 0.05


def welch(a, b):
    """t de Welch. Tamanho do efeito: d de Cohen (desvio combinado)."""
    t, p = stats.ttest_ind(a, b, equal_var=False)
    desvio = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    d = (np.mean(a) - np.mean(b)) / desvio
    return {"teste": "Welch", "estatistica": float(t), "p_valor": float(p),
            "efeito": float(d), "nome_efeito": "d de Cohen"}


def mann_whitney(a, b):
    """Mann-Whitney. Tamanho do efeito: delta de Cliff (de -1 a 1)."""
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    delta = 2 * u / (len(a) * len(b)) - 1
    return {"teste": "Mann-Whitney", "estatistica": float(u), "p_valor": float(p),
            "efeito": float(delta), "nome_efeito": "delta de Cliff"}


def aplicar_testes(a, b, alfa=ALFA):
    resultados = [welch(a, b), mann_whitney(a, b)]
    for r in resultados:
        r["rejeita_h0"] = r["p_valor"] < alfa
    return resultados


if __name__ == "__main__":
    from src.simulacao import gerar_grupos, ler_cenario

    grupos = gerar_grupos(ler_cenario())
    for r in aplicar_testes(grupos["sem_bot"], grupos["com_bot"]):
        print(f"{r['teste']}: estatistica={r['estatistica']:.3f}, p={r['p_valor']:.4f}, "
              f"{r['nome_efeito']}={r['efeito']:.3f}, rejeita H0={r['rejeita_h0']}")
