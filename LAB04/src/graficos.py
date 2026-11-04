"""Gráficos do Lab04. fig_g1 fica com o Arthur, fig_g2 com o Pedro."""
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Mesma cor para cada teste em todos os gráficos
CORES = {"Welch": "#1f77b4", "Mann-Whitney": "#ff7f0e"}
ALFA = 0.05


def _gl_welch(a, b):
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    return (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))


def _painel(ax, dist, observado, cor, titulo, rotulo_x):
    critico = dist.ppf(1 - ALFA / 2)
    x = np.linspace(-4.5, 4.5, 500)
    y = dist.pdf(x)
    ax.plot(x, y, color="black", lw=1.5, label="Distribuição sob H₀")

    # p-valor do exemplo como área
    p = 2 * dist.sf(abs(observado))
    ax.fill_between(x, y, where=np.abs(x) >= abs(observado), color=cor, alpha=0.35,
                    label=f"p-valor do exemplo ≈ {p:.3f}")
    ax.axvline(observado, color=cor, ls="--", lw=1.5, label=f"Valor observado = {observado:.2f}")

    # Região de rejeição (bicaudal, alfa = 5%), desenhada por cima com hachura
    ax.fill_between(x, y, where=np.abs(x) >= critico, facecolor="none", edgecolor="red",
                    hatch="///", lw=0, label=f"Região de rejeição (α = {ALFA}, |valor| ≥ {critico:.2f})")
    for c in (-critico, critico):
        ax.axvline(c, color="red", lw=1)

    ax.set_title(titulo)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel("Densidade")
    ax.set_ylim(0, 0.6)
    ax.legend(fontsize=7, loc="upper right")


def fig_g2(a, b):
    """G2: estatística de cada teste sob H₀, região de rejeição e p-valor de um exemplo."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Welch: t segue uma t de Student com gl de Welch-Satterthwaite
    t, _ = stats.ttest_ind(a, b, equal_var=False)
    gl = _gl_welch(a, b)
    _painel(ax1, stats.t(gl), t, CORES["Welch"],
            f"Welch: estatística t sob H₀ (gl ≈ {gl:.1f})", "Estatística t (sem unidade)")

    # Mann-Whitney: U padronizado segue aproximadamente uma normal padrão
    n1, n2 = len(a), len(b)
    u, _ = stats.mannwhitneyu(a, b, alternative="two-sided")
    z = (u - n1 * n2 / 2) / np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    _painel(ax2, stats.norm(), z, CORES["Mann-Whitney"],
            "Mann-Whitney: U padronizado (z) sob H₀", "Estatística z (sem unidade)")

    fig.suptitle("G2: distribuição da estatística sob H₀ (teste bicaudal, α = 5%)")
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    from src.simulacao import gerar_grupos, ler_cenario

    grupos = gerar_grupos(ler_cenario())
    fig_g2(grupos["sem_bot"], grupos["com_bot"]).savefig("figs/g2.png", dpi=150)
    print("figs/g2.png salvo")
