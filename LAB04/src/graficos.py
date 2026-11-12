"""Gráficos do Lab04. fig_g1 fica com o Arthur; fig_g2, fig_g3 e fig_g4 ficam aqui.

O G3 e o G4 recebem a tabela de taxas de rejeição já lida (``src.resultados.ler_taxas``)
e desenham o que encontrarem nela: com a Q3 ainda pendente, sai só o cenário real, e
quando o ``resultados/q3.csv`` entrar os painéis e as barras das outras situações
aparecem sem precisar mexer aqui.
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
from scipy import stats

from src import resultados

# Mesma cor para cada teste em todos os gráficos, inclusive na página publicada:
# quem define é o src.resultados, para não haver duas listas de cores no repositório.
CORES = resultados.CORES
ALFA = 0.05
N_REP = 10_000
PODER_ALVO = 0.80

# Margem de erro da proporção estimada em N_REP repetições, em torno de 5%: é o quanto
# uma barra do G3 pode se afastar de 5% só por causa da simulação.
MARGEM = 1.96 * np.sqrt(ALFA * (1 - ALFA) / N_REP)


def _virgula(texto: str) -> str:
    """Decimal com vírgula, como no resto do trabalho."""
    return texto.replace(".", ",")


def _milhar(numero: int) -> str:
    """10000 -> '10.000'."""
    return f"{numero:,}".replace(",", ".")


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


def fig_g3(taxas):
    """G3: erro tipo I dos dois testes em cada situação, com a linha em 5%.

    ``taxas`` é a tabela de ``src.resultados``; aqui usamos só as linhas de razão = 1,
    que são as de H₀ verdadeira (Q1 no cenário real e Q3 nas outras situações).
    """
    tabela = resultados.erro_tipo_i(taxas)
    if tabela.empty:
        raise ValueError("o G3 precisa das linhas de razão = 1 (H₀ verdadeira)")

    situacoes = resultados.situacoes(tabela)
    x = np.arange(len(situacoes))
    largura = 0.8 / len(CORES)

    fig, ax = plt.subplots(figsize=(3.4 + 2.2 * len(situacoes), 4.8))
    ax.axhspan(ALFA - MARGEM, ALFA + MARGEM, color="red", alpha=0.10,
               label="margem da simulação: ±" + _virgula(f"{MARGEM * 100:.1f}") + " p.p.")
    ax.axhline(ALFA, color="red", ls="--", lw=1.4, label=f"α = {ALFA:.0%} (esperado)")

    teto = ALFA + MARGEM
    for i, (teste, cor) in enumerate(CORES.items()):
        por_situacao = tabela[tabela["teste"] == teste].set_index("situacao")["taxa_rejeicao"]
        alturas = [por_situacao.get(s, np.nan) for s in situacoes]
        teto = max(teto, np.nanmax(alturas))
        barras = ax.bar(x + (i - (len(CORES) - 1) / 2) * largura, alturas, largura,
                        color=cor, label=teste, edgecolor="white")
        ax.bar_label(barras, padding=2, fontsize=8,
                     labels=[_virgula(f"{a:.2%}") if np.isfinite(a) else "" for a in alturas])

    ax.set_title(f"G3: erro tipo I por situação ({_milhar(N_REP)} repetições por barra)")
    ax.set_xlabel("Situação simulada")
    ax.set_ylabel("Rejeições com H₀ verdadeira (% das repetições)")
    ax.set_xticks(x, resultados.rotulos(tabela), fontsize=9)
    ax.set_xlim(-0.75, len(situacoes) - 0.25)
    ax.set_ylim(0, teto * 1.30)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    # Os dois testes primeiro na legenda; as referências (5% e margem) depois.
    handles, nomes = ax.get_legend_handles_labels()
    ordem = sorted(range(len(nomes)), key=lambda i: nomes[i] not in CORES)
    ax.legend([handles[i] for i in ordem], [nomes[i] for i in ordem],
              fontsize=8, loc="upper left")
    fig.tight_layout()
    return fig


def fig_g4(taxas):
    """G4: curvas de poder dos dois testes, um painel por situação.

    Eixo x invertido de propósito: a razão entre as medianas vai de 1 (sem efeito) a
    0,2 (efeito grande), então o efeito cresce da esquerda para a direita.
    """
    tabela = resultados.ordenar(taxas)
    situacoes = resultados.situacoes(tabela)
    rotulos = resultados.rotulos(tabela)

    fig, eixos = plt.subplots(1, len(situacoes), sharey=True, squeeze=False,
                              figsize=(1.2 + 4.2 * len(situacoes), 4.6))
    for ax, situacao, rotulo in zip(eixos[0], situacoes, rotulos):
        sub = tabela[tabela["situacao"] == situacao]
        for teste, cor in CORES.items():
            linha = sub[sub["teste"] == teste].sort_values("razao", ascending=False)
            ax.plot(linha["razao"], linha["taxa_rejeicao"], marker="o", ms=5, lw=1.8,
                    color=cor, label=teste)
        ax.axhline(ALFA, color="red", ls="--", lw=1)
        ax.axhline(PODER_ALVO, color="grey", ls=":", lw=1)
        ax.set_title(rotulo.replace("\n", " "), fontsize=10)
        ax.set_xlabel("Razão entre as medianas (tratamento ÷ controle)\n← sem efeito"
                      "        efeito maior →")
        ax.set_xticks(sorted(sub["razao"].unique()))
        ax.invert_xaxis()
        ax.grid(alpha=0.25)
        ax.set_axisbelow(True)

    eixos[0][0].set_ylabel("Rejeições — poder do teste (% das repetições)")
    eixos[0][0].set_ylim(0, 1.03)
    eixos[0][0].yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    eixos[0][0].legend(
        handles=[Line2D([], [], color=cor, marker="o", ms=5, label=teste)
                 for teste, cor in CORES.items()]
        + [Line2D([], [], color="red", ls="--", label=f"α = {ALFA:.0%}"),
           Line2D([], [], color="grey", ls=":", label=f"poder de {PODER_ALVO:.0%}")],
        fontsize=8, loc="upper left")

    fig.suptitle(f"G4: curvas de poder ({_milhar(N_REP)} repetições por ponto, "
                 f"α = {ALFA:.0%})")
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    from src.simulacao import gerar_grupos, ler_cenario

    grupos = gerar_grupos(ler_cenario())
    fig_g2(grupos["sem_bot"], grupos["com_bot"]).savefig("docs/g2_estatistica_sob_h0.png",
                                                         dpi=150)
    print("docs/g2_estatistica_sob_h0.png salvo")

    taxas = resultados.ler_taxas()
    fig_g3(taxas).savefig("docs/g3_erro_tipo_i.png", dpi=150)
    fig_g4(taxas).savefig("docs/g4_curvas_de_poder.png", dpi=150)
    print("docs/g3_erro_tipo_i.png e docs/g4_curvas_de_poder.png salvos")
