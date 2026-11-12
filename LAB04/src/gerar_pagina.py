"""Gera a página HTML do dashboard publicado (GitHub Pages).

O arquivo servido em https://candian15.github.io/LabExpGRP/ é o ``index.html`` da raiz
do repositório, e é este script que o escreve. Todos os números e todos os gráficos saem
dos arquivos do repositório:

* ``config/cenario.yaml``: pergunta, distribuição, μ, σ, mediana, semente e razões;
* ``data/dados_reais.csv`` e ``data/estatisticas_descritivas.csv``: os 60 PRs coletados;
* ``resultados/q1.csv``, ``q2.csv`` e ``q3.csv``: erro tipo I e poder (Q1, Q2 e Q3);
* ``resultados/dados_reais.csv``: os dois testes aplicados aos PRs reais;
* ``src.simulacao`` + ``src.testes``: o conjunto simulado que serve de exemplo no G2;
* ``src.monte_carlo``: as taxas com α = 0,01 que a pergunta 12 da apresentação usa.

Nada é digitado à mão: trocar um CSV e rodar de novo muda a página.

A página é feita para ser apresentada em projetor: tema claro fixo, fontes grandes, nada
que dependa de clique, e os gráficos são SVG gerado aqui (sem JavaScript e sem CDN), para
que ela abra em qualquer lugar e não tenha como quebrar no console.

Uso (a partir de LAB04/):  python -m src.gerar_pagina
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src import resultados
from src.dados_reais import interpretar_efeito
from src.graficos_g1 import COR_GRUPO, ROTULO_GRUPO, simular_para_g1
from src.monte_carlo import N_REP, taxas_de_amostras
from src.simulacao import gerar_grupos, ler_cenario
from src.testes import ALFA, aplicar_testes

RAIZ = Path(__file__).resolve().parent.parent      # LAB04/
SAIDA = RAIZ.parent / "index.html"                 # o arquivo que o GitHub Pages serve

REPOSITORIO = "https://github.com/candian15/LabExpGRP"
PROJECTS = "https://github.com/users/candian15/projects/2"
DASHBOARD = "https://candian15.github.io/LabExpGRP/"

# Cor de cada teste, a mesma das figuras do matplotlib: quem define é o src.resultados.
# Os grupos (sem bot e com bot) usam as cores do src.graficos_g1, de propósito diferentes.
COR = resultados.CORES
COR_ALFA = "#b91c1c"      # a linha dos 5% e a região de rejeição
COR_PODER = "#15803d"     # a linha dos 80% de poder
CINZA = "#4b5563"
GRADE = "#dde2ea"
ALFA_ESTRITO = 0.01       # o α alternativo da pergunta 12
PODER_ALVO = 0.80
MARGEM = 1.96 * np.sqrt(ALFA * (1 - ALFA) / N_REP)   # ±0,4 p.p. em 10.000 repetições

# Quem narra cada seção nos 7 minutos de apresentação.
APRESENTA = {s: "Santana" for s in (1, 2, 3, 6)} | {s: "Pedro" for s in (4, 5, 7)}

# Quem responde cada uma das 15 perguntas da seção 5 do enunciado. A regra é que cada
# integrante responda a pelo menos 4; as perguntas foram para quem fez a parte
# correspondente (Arthur: coleta, parâmetros, Q3 e dados reais).
RESPONDE = ({n: "Santana" for n in (1, 2, 5, 6, 7)}
            | {n: "Pedro" for n in (8, 9, 10, 12, 13, 15)}
            | {n: "Arthur" for n in (3, 4, 11, 14)})


# --------------------------------------------------------------------- formatação
def vg(texto: str) -> str:
    """Decimal com vírgula, como no resto do trabalho."""
    return texto.replace(".", ",")


def pct(x: float, casas: int = 1) -> str:
    return vg(f"{x * 100:.{casas}f}") + "%"


def num(x: float, casas: int = 1) -> str:
    return vg(f"{x:.{casas}f}")


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def p_valor(p: float) -> str:
    return "p &lt; 0,001" if p < 0.001 else "p = " + vg(f"{p:.3f}")


# ------------------------------------------------------------------ peças de SVG
def _txt(x, y, t, tam=16, cor=CINZA, anc="middle", peso="400", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tam}" fill="{cor}" '
            f'text-anchor="{anc}" font-weight="{peso}"{extra}>{t}</text>')


def _ln(x1, y1, x2, y2, cor=GRADE, larg=1, tracos=""):
    d = f' stroke-dasharray="{tracos}"' if tracos else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{cor}" stroke-width="{larg}"{d}/>')


def _ret(x, y, w, h, cor, opac=1.0, borda="none", raio=0):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" '
            f'rx="{raio}" fill="{cor}" fill-opacity="{opac}" stroke="{borda}"/>')


def _area(pontos, cor, opac, contorno="none", larg=0):
    d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pontos) + "Z"
    return (f'<path d="{d}" fill="{cor}" fill-opacity="{opac}" stroke="{contorno}" '
            f'stroke-width="{larg}"/>')


def _curva(pontos, cor, larg=3, tracos=""):
    d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pontos)
    t = f' stroke-dasharray="{tracos}"' if tracos else ""
    return (f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="{larg}" '
            f'stroke-linejoin="round"{t}/>')


def _svg(w, h, corpo, descricao):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
            f'aria-label="{descricao}" font-family="inherit">{corpo}</svg>')


def _eixo_y_pct(x0, x1, y_de, valores, rotulo_de):
    """Linhas de grade horizontais com o rótulo em porcentagem à esquerda."""
    s = ""
    for valor in valores:
        y = y_de(valor)
        s += _ln(x0, y, x1, y)
        s += _txt(x0 - 10, y + 6, rotulo_de(valor), 15, CINZA, "end")
    return s


# ------------------------------------------------------------------- G1: os dados
def svg_g1(reais: pd.DataFrame, simulados: pd.DataFrame, col="horas_ate_merge") -> str:
    """Histograma de cada grupo, dados reais na linha de cima e simulados na de baixo."""
    grupos = [g for g in ("sem_bot", "com_bot") if g in set(reais["grupo"])]
    x = reais[col].to_numpy(float)
    x = x[x > 0]
    lo = float(np.floor(np.log10(x.min())) - 0.5)
    hi = float(np.ceil(np.log10(x.max())) + 0.5)
    bins = np.logspace(lo, hi, 20)

    painel = {}
    for g in grupos:
        for fonte, df in (("reais", reais), ("simulados", simulados)):
            v = df.loc[df["grupo"] == g, col].to_numpy(float)
            alturas, _ = np.histogram(np.clip(v, bins[0], bins[-1]), bins=bins)
            painel[(g, fonte)] = (alturas / len(v), float(np.median(v)), len(v))
    topo = max(p.max() for p, _, _ in painel.values()) * 1.20

    W, H = 1060, 584
    pw, ph = 530, 268
    ml, mr, mt, mb = 78, 18, 58, 58
    corpo = ""
    for j, g in enumerate(grupos):
        for i, fonte in enumerate(("reais", "simulados")):
            px, py = j * pw, i * ph + 8
            x0, x1 = px + ml, px + pw - mr
            y0, y1 = py + mt, py + ph - mb
            alturas, mediana, n = painel[(g, fonte)]

            def X(valor, x0=x0, x1=x1):
                return x0 + (np.log10(valor) - lo) / (hi - lo) * (x1 - x0)

            def Y(valor, y0=y0, y1=y1):
                return y1 - valor / topo * (y1 - y0)

            corpo += _eixo_y_pct(x0, x1, Y, [0, 0.1, 0.2, 0.3],
                                 lambda t: vg(f"{t * 100:.0f}") + "%")
            for k, altura in enumerate(alturas):
                corpo += _ret(X(bins[k]), Y(altura), X(bins[k + 1]) - X(bins[k]),
                              y1 - Y(altura), COR_GRUPO[g], 0.90 if fonte == "reais" else 0.45,
                              "#ffffff")
            corpo += _ln(X(mediana), y0 - 4, X(mediana), y1, "#111827", 2.5, "7 5")
            corpo += _txt(X(mediana), y0 - 10, "mediana " + num(mediana) + " h", 14,
                          "#111827", "middle", "600")
            corpo += _ln(x0, y1, x1, y1, "#9aa3b2", 1.5)
            for t in (0.01, 0.1, 1, 10, 100, 1000):
                corpo += _txt(X(t), y1 + 24, vg(str(t)) + " h", 15)
            nome_fonte = "dados reais" if fonte == "reais" else "dados simulados"
            corpo += _txt(x0 - 4, py + 24,
                          f"{ROTULO_GRUPO[g]}: {nome_fonte} (n = {milhar(n)})",
                          18, "#111827", "start", "700")
            if i == 1:
                corpo += _txt((x0 + x1) / 2, y1 + 50,
                              "Tempo até o merge (horas, escala log)", 16, "#111827")
            if j == 0:
                corpo += (f'<text x="{px + 24}" y="{(y0 + y1) / 2:.1f}" font-size="16" '
                          f'fill="#111827" text-anchor="middle" '
                          f'transform="rotate(-90 {px + 24} {(y0 + y1) / 2:.1f})">'
                          f'Proporção de PRs</text>')

    legenda = (_ret(14, H - 26, 20, 16, COR_GRUPO["sem_bot"], 0.90)
               + _txt(42, H - 13, "sem bot", 15, "#111827", "start")
               + _ret(120, H - 26, 20, 16, COR_GRUPO["com_bot"], 0.90)
               + _txt(148, H - 13, "com bot", 15, "#111827", "start")
               + _ret(232, H - 26, 20, 16, COR_GRUPO["sem_bot"], 0.45)
               + _ret(256, H - 26, 20, 16, COR_GRUPO["com_bot"], 0.45)
               + _txt(284, H - 13, "tom claro = simulados", 15, "#111827", "start")
               + _ln(470, H - 18, 500, H - 18, "#111827", 2.5, "7 5")
               + _txt(508, H - 13, "mediana do grupo", 15, "#111827", "start"))
    return _svg(W, H, corpo + legenda,
                "G1: histograma do tempo até o merge de cada grupo, dados reais e simulados")


# ----------------------------------------------------- G2: como os testes funcionam
def _gl_welch(a, b):
    """Graus de liberdade de Welch-Satterthwaite (o mesmo cálculo do src.graficos)."""
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    return (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))


def _painel_g2(px, dist, observado, teste, titulo, rotulo_x, rotulo_obs, mostrar_y):
    pw, ph = 530, 372
    ml, mr, mt, mb = 76, 22, 50, 74
    x0, x1 = px + ml, px + pw - mr
    y0, y1 = mt, ph - mb
    critico = float(dist.ppf(1 - ALFA / 2))
    p = float(2 * dist.sf(abs(observado)))
    cor = COR[teste]
    lim = 4.6
    topo = 0.46

    def X(v):
        return x0 + (v + lim) / (2 * lim) * (x1 - x0)

    def Y(v):
        return y1 - v / topo * (y1 - y0)

    malha = np.linspace(-lim, lim, 320)
    dens = dist.pdf(malha)

    def faixa(de, ate):
        sel = (malha >= de) & (malha <= ate)
        if not sel.any():
            return []
        return ([(X(de), y1)] + [(X(v), Y(d)) for v, d in zip(malha[sel], dens[sel])]
                + [(X(ate), y1)])

    s = _eixo_y_pct(x0, x1, Y, [0, 0.1, 0.2, 0.3, 0.4], lambda t: vg(f"{t:.1f}"))
    # região de rejeição (as duas pontas, 5% no total)
    for de, ate in ((-lim, -critico), (critico, lim)):
        s += _area(faixa(de, ate), COR_ALFA, 0.16)
    # o p-valor do exemplo, também como área, nas duas pontas
    for de, ate in ((-lim, -abs(observado)), (abs(observado), lim)):
        s += _area(faixa(de, ate), cor, 0.85, cor, 1.5)
    s += _curva([(X(v), Y(d)) for v, d in zip(malha, dens)], "#111827", 2.5)
    for c in (-critico, critico):
        s += _ln(X(c), Y(float(dist.pdf(c))), X(c), y1, COR_ALFA, 2)
    s += _ln(X(observado), y0 - 2, X(observado), y1, cor, 3)
    s += _txt(X(observado) - 10, y0 + 14, rotulo_obs, 17, cor, "end", "700")
    s += _ln(x0, y1, x1, y1, "#9aa3b2", 1.5)
    for t in (-4, -2, 0, 2, 4):
        s += _txt(X(t), y1 + 24, vg(str(t)), 15)
    # seta apontando para a área do p-valor
    seta_x, seta_y = X(abs(observado)) + 6, Y(0.02)
    s += (f'<path d="M{X(lim * 0.52):.1f} {Y(0.21):.1f} Q {seta_x + 28:.1f} {Y(0.12):.1f} '
          f'{seta_x:.1f} {seta_y:.1f}" fill="none" stroke="{cor}" stroke-width="2"/>')
    s += (f'<path d="M{seta_x:.1f} {seta_y:.1f} l 9 -9 l 2 12 z" fill="{cor}"/>')
    s += _txt(X(lim * 0.52) - 6, Y(0.215), "área = p-valor = " + vg(f"{p:.4f}"), 15, cor,
              "end", "700")
    s += _txt(x0 - 4, 26, titulo, 17, "#111827", "start", "700")
    s += _txt((x0 + x1) / 2, y1 + 50, rotulo_x, 16, "#111827")
    if mostrar_y:
        s += (f'<text x="{px + 22}" y="{(y0 + y1) / 2:.1f}" font-size="16" fill="#111827" '
              f'text-anchor="middle" transform="rotate(-90 {px + 22} {(y0 + y1) / 2:.1f})">'
              f'Densidade</text>')
    return s, critico, p


def svg_g2(a, b):
    """Distribuição da estatística sob H₀, região de rejeição e p-valor como área."""
    t = float(stats.ttest_ind(a, b, equal_var=False).statistic)
    gl = _gl_welch(a, b)
    n1, n2 = len(a), len(b)
    u = float(stats.mannwhitneyu(a, b, alternative="two-sided").statistic)
    z = (u - n1 * n2 / 2) / np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)

    esq, crit_t, p_t = _painel_g2(0, stats.t(gl), t, "Welch",
                                  f"Welch: t sob H₀ (t de Student, gl ≈ {num(gl)})",
                                  "Estatística t (sem unidade)", "t = " + num(t, 2), True)
    dir_, crit_z, p_z = _painel_g2(530, stats.norm(), z, "Mann-Whitney",
                                   "Mann-Whitney: U padronizado sob H₀ (normal padrão)",
                                   "Estatística z (sem unidade)", "z = " + num(z, 2), False)
    W, H = 1060, 430
    legenda = (_ret(14, H - 30, 20, 16, COR_ALFA, 0.16, COR_ALFA)
               + _txt(42, H - 17, f"região de rejeição (α = 5%, as duas pontas)", 15,
                      "#111827", "start")
               + _ret(392, H - 30, 20, 16, COR["Welch"], 0.75)
               + _ret(416, H - 30, 20, 16, COR["Mann-Whitney"], 0.75)
               + _txt(444, H - 17, "área do p-valor do exemplo", 15, "#111827", "start")
               + _ln(700, H - 22, 700, H - 34, "#111827", 3)
               + _txt(712, H - 17, "valor observado no conjunto simulado", 15, "#111827",
                      "start"))
    return (_svg(W, H, esq + dir_ + legenda,
                 "G2: distribuição da estatística de cada teste sob H zero, com a região "
                 "de rejeição sombreada e o p-valor do exemplo marcado como área"),
            {"t": t, "gl": gl, "u": u, "z": z, "crit_t": crit_t, "crit_z": crit_z,
             "p_t": p_t, "p_z": p_z})


# ----------------------------------------------------------------- G3: erro tipo I
def _rotulo(situacao, n, sigma):
    nome = resultados.NOMES.get(situacao, str(situacao).replace("_", " "))
    return nome, f"σ = {num(float(sigma), 2)} · n = {int(n)}"


def svg_g3(taxas: pd.DataFrame) -> str:
    """Barras do erro tipo I de cada teste em cada situação, com a linha em 5%."""
    tabela = resultados.erro_tipo_i(taxas)
    situacoes = resultados.situacoes(tabela)
    topo = max(ALFA + MARGEM, float(tabela["taxa_rejeicao"].max())) * 1.38

    W, H = 1060, 436
    ml, mr, mt, mb = 104, 26, 48, 92
    x0, x1, y0, y1 = ml, W - mr, mt, H - mb
    largura_grupo = (x1 - x0) / len(situacoes)
    largura_barra = largura_grupo * 0.27

    def Y(v):
        return y1 - v / topo * (y1 - y0)

    s = _eixo_y_pct(x0, x1, Y, [0, 0.02, 0.04, 0.06], lambda t: vg(f"{t * 100:.0f}") + "%")
    s += _ret(x0, Y(ALFA + MARGEM), x1 - x0, Y(ALFA - MARGEM) - Y(ALFA + MARGEM),
              COR_ALFA, 0.12)
    s += _ln(x0, Y(ALFA), x1, Y(ALFA), COR_ALFA, 2.5, "9 6")

    for i, situacao in enumerate(situacoes):
        centro = x0 + (i + 0.5) * largura_grupo
        linhas = tabela[tabela["situacao"] == situacao]
        nome, detalhe = _rotulo(situacao, linhas["n"].iloc[0], linhas["sigma"].iloc[0])
        s += _txt(centro, y1 + 32, nome, 18, "#111827", "middle", "700")
        s += _txt(centro, y1 + 54, detalhe, 15)
        for k, (teste, cor) in enumerate(COR.items()):
            alvo = linhas[linhas["teste"] == teste]
            if alvo.empty:
                continue
            valor = float(alvo["taxa_rejeicao"].iloc[0])
            bx = centro + (k - 0.5) * largura_barra * 1.12 - largura_barra / 2
            s += _ret(bx, Y(valor), largura_barra, y1 - Y(valor), cor, 1.0, "none", 4)
            s += _txt(bx + largura_barra / 2, Y(valor) - 10, pct(valor, 2), 17, cor,
                      "middle", "700")

    s += _ln(x0, y1, x1, y1, "#9aa3b2", 1.5)
    s += _txt((x0 + x1) / 2, H - 16, "Situação simulada", 17, "#111827")
    s += (f'<text x="26" y="{(y0 + y1) / 2:.1f}" font-size="16" fill="#111827" '
          f'text-anchor="middle" transform="rotate(-90 26 {(y0 + y1) / 2:.1f})">'
          f'Rejeições com H₀ verdadeira (% das repetições)</text>')
    legenda = ""
    for k, (teste, cor) in enumerate(COR.items()):
        legenda += _ret(x0 + k * 190, 18, 20, 16, cor)
        legenda += _txt(x0 + 28 + k * 190, 31, teste, 16, "#111827", "start", "600")
    legenda += _ln(x0 + 390, 26, x0 + 420, 26, COR_ALFA, 2.5, "9 6")
    legenda += _txt(x0 + 428, 31, "α = 5% (o esperado)", 16, COR_ALFA, "start", "700")
    legenda += _ret(x0 + 640, 18, 20, 16, COR_ALFA, 0.12, COR_ALFA)
    legenda += _txt(x0 + 668, 31, "margem da simulação: ±" + vg(f"{MARGEM * 100:.1f}") + " p.p.",
                    16, "#111827", "start")
    return _svg(W, H, legenda + s,
                "G3: proporção de rejeições com H zero verdadeira para cada teste em cada "
                "situação simulada, com a linha de 5%")


# ---------------------------------------------------------------------- G4: poder
def svg_g4(taxas: pd.DataFrame) -> str:
    """Curvas de poder dos dois testes, as quatro situações visíveis ao mesmo tempo."""
    tabela = resultados.ordenar(taxas)
    situacoes = resultados.situacoes(tabela)
    razoes = sorted(tabela["razao"].unique(), reverse=True)

    pw, ph = 530, 312
    colunas = 2
    linhas_grade = (len(situacoes) + colunas - 1) // colunas
    W, H = pw * colunas, ph * linhas_grade + 46
    ml, mr, mt, mb = 86, 26, 60, 72
    corpo = ""
    for i, situacao in enumerate(situacoes):
        px, py = (i % colunas) * pw, (i // colunas) * ph + 42
        x0, x1 = px + ml, px + pw - mr
        y0, y1 = py + mt, py + ph - mb
        sub = tabela[tabela["situacao"] == situacao]
        nome, detalhe = _rotulo(situacao, sub["n"].iloc[0], sub["sigma"].iloc[0])

        def X(r, x0=x0, x1=x1):
            return x0 + (1.0 - r) / (1.0 - min(razoes)) * (x1 - x0)

        def Y(v, y0=y0, y1=y1):
            return y1 - v * (y1 - y0)

        corpo += _eixo_y_pct(x0, x1, Y, [0, 0.25, 0.5, 0.75, 1.0],
                             lambda t: vg(f"{t * 100:.0f}") + "%")
        corpo += _ln(x0, Y(PODER_ALVO), x1, Y(PODER_ALVO), COR_PODER, 2, "8 6")
        corpo += _ln(x0, Y(ALFA), x1, Y(ALFA), COR_ALFA, 2, "8 6")
        for teste, cor in COR.items():
            pontos = []
            for r in razoes:
                alvo = sub[(sub["teste"] == teste) & (sub["razao"] == r)]
                if not alvo.empty:
                    pontos.append((X(r), Y(float(alvo["taxa_rejeicao"].iloc[0]))))
            if not pontos:
                continue
            corpo += _curva(pontos, cor, 3.4)
            for cx, cy in pontos:
                corpo += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{cor}" '
                          f'stroke="#ffffff" stroke-width="2"/>')
        corpo += _ln(x0, y1, x1, y1, "#9aa3b2", 1.5)
        for r in razoes:
            corpo += _txt(X(r), y1 + 24, vg(f"{r:.1f}"), 15)
        corpo += _txt(x0 - 4, py + 26, nome, 19, "#111827", "start", "700")
        corpo += _txt(x0 - 4, py + 46, detalhe, 14, CINZA, "start")
        corpo += _txt((x0 + x1) / 2, y1 + 50, "Razão entre as medianas (com bot ÷ sem bot)",
                      16, "#111827")
        corpo += (f'<text x="{px + 24}" y="{(y0 + y1) / 2:.1f}" font-size="16" '
                  f'fill="#111827" text-anchor="middle" '
                  f'transform="rotate(-90 {px + 24} {(y0 + y1) / 2:.1f})">'
                  f'Poder (% de rejeições)</text>')

    legenda = ""
    for k, (teste, cor) in enumerate(COR.items()):
        legenda += _ln(82 + k * 214, 20, 120 + k * 214, 20, cor, 3.4)
        legenda += (f'<circle cx="{101 + k * 214}" cy="20" r="6" fill="{cor}" '
                    f'stroke="#ffffff" stroke-width="2"/>')
        legenda += _txt(130 + k * 214, 26, teste, 16, "#111827", "start", "600")
    legenda += _ln(520, 20, 558, 20, COR_PODER, 2.5, "8 6")
    legenda += _txt(566, 26, "poder de 80% (a meta usual)", 16, COR_PODER, "start", "600")
    legenda += _ln(800, 20, 838, 20, COR_ALFA, 2.5, "8 6")
    legenda += _txt(846, 26, "α = 5%", 16, COR_ALFA, "start", "600")
    return _svg(W, H, legenda + corpo,
                "G4: curvas de poder dos dois testes por tamanho do efeito, um painel "
                "para cada situação simulada")


# ------------------------------------------------------ os dados que a página usa
def taxa(taxas, situacao, razao, teste) -> float | None:
    linha = taxas[(taxas["situacao"] == situacao) & (taxas["razao"] == razao)
                  & (taxas["teste"] == teste)]
    return None if linha.empty else float(linha["taxa_rejeicao"].iloc[0])


def taxas_com_alfa_estrito(cenario, razoes=(1.0, 0.2), alfa=ALFA_ESTRITO):
    """As taxas do cenário real com outro α, para a pergunta 12 da apresentação.

    Mesma convenção do ``src.monte_carlo`` (controle com μ e σ reais, tratamento com
    μ + ln(razão)) e semente derivada da do cenário, então o número não muda de uma
    execução para a outra.
    """
    controle = cenario["grupos"][cenario["controle"]]
    mu, sigma, n = controle["mu"], controle["sigma"], cenario["n_por_grupo"]
    rng = np.random.default_rng([cenario["semente"], 12])
    saida = {}
    for razao in razoes:
        A = rng.lognormal(mu, sigma, (N_REP, n))
        B = rng.lognormal(mu + np.log(razao), sigma, (N_REP, n))
        saida[razao] = taxas_de_amostras(A, B, alfa)
    return saida


def carregar() -> dict:
    cenario = ler_cenario(RAIZ / "config" / "cenario.yaml")
    reais = pd.read_csv(RAIZ / "data" / "dados_reais.csv")
    descritivas = pd.read_csv(RAIZ / "data" / "estatisticas_descritivas.csv")
    taxas = resultados.ler_taxas(RAIZ / "resultados")
    nos_reais = pd.read_csv(RAIZ / "resultados" / "dados_reais.csv")

    grupos = gerar_grupos(cenario)
    exemplo = aplicar_testes(grupos[cenario["controle"]], grupos[cenario["tratamento"]])
    simulados = simular_para_g1(cenario, np.random.default_rng(cenario["semente"]))

    g2, info_g2 = svg_g2(grupos[cenario["controle"]], grupos[cenario["tratamento"]])
    return {
        "cenario": cenario, "reais": reais, "descritivas": descritivas, "taxas": taxas,
        "nos_reais": nos_reais, "exemplo": exemplo, "grupos": grupos,
        "g1": svg_g1(reais, simulados), "g2": g2, "info_g2": info_g2,
        "g3": svg_g3(taxas), "g4": svg_g4(taxas),
        "estrito": taxas_com_alfa_estrito(cenario),
    }


# -------------------------------------------------------------- peças de HTML
def _tabela(cabecalho, linhas, classe="") -> str:
    cls = f' class="{classe}"' if classe else ""
    cab = "".join(f"<th>{c}</th>" for c in cabecalho)
    corpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>"
                    for linha in linhas)
    return f"<table{cls}><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table>"


def _secao(ident, numero, titulo, legenda, kpis, conteudo) -> str:
    """Uma seção do enunciado: cabeçalho, quem apresenta, a faixa de números e o conteúdo."""
    quem = APRESENTA.get(numero, "Santana")
    return (f'<section id="s{ident}"><div class="cab">'
            f'<h2><span class="n">{numero}</span>{titulo}</h2>'
            f'<span class="quem">apresenta: {quem}</span></div>'
            f'<p class="leg">{legenda}</p>{kpis}{conteudo}</section>')


def _kpis(*cartoes) -> str:
    """A faixa de indicadores no topo da seção, que é o que o olho pega primeiro."""
    return f'<div class="kpis">{"".join(cartoes)}</div>'


def _tile(rotulo, valor, classe="", sub="") -> str:
    """Cartão de um número só."""
    return (f'<div class="tile {classe}"><span class="rot">{rotulo}</span>'
            f'<b>{valor}</b><span class="vs">{sub}</span></div>')


def _duo(rotulo, valor_a, classe_a, valor_b, classe_b, sub="", cor_a=None, cor_b=None) -> str:
    """Cartão que compara dois números lado a lado, que é a forma do trabalho inteiro."""
    def lado(valor, classe, cor):
        estilo = f' style="color:{cor}"' if cor else ""
        return f'<i class="{classe}"{estilo}>{valor}</i>'

    return (f'<div class="tile"><span class="rot">{rotulo}</span>'
            f'<div class="duo">{lado(valor_a, classe_a, cor_a)}<s>×</s>'
            f'{lado(valor_b, classe_b, cor_b)}</div>'
            f'<span class="vs">{sub}</span></div>')


def _barra(valor, cor, maximo=1.0) -> str:
    """Barra proporcional dentro da célula da tabela, para comparar de relance."""
    largura = min(max(valor / maximo, 0.0), 1.0) * 100
    return (f'<div class="bar"><span style="width:{largura:.1f}%;background:{cor}"></span>'
            f'<em>{pct(valor, 2 if maximo < 0.5 else 1)}</em></div>')


def _nota(texto) -> str:
    return f'<div class="nota">{texto}</div>'


def _pill(texto, tipo) -> str:
    return f'<span class="pill {tipo}">{texto}</span>'


CSS = """
:root{color-scheme:light;--bg:#eef1f6;--card:#ffffff;--tx:#0f172a;--mu:#64748b;
--bd:#dbe1ea;--w:#e8590c;--m:#2563eb;--ok:#15803d;--al:#b91c1c;--ac:#5b21b6;
--wbg:#fff2e8;--mbg:#eaf1fe;--okbg:#ecfdf5}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);
font:18px/1.55 "Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif}
.wrap{max-width:1360px;margin:0 auto;padding:0 28px}
nav{position:sticky;top:0;z-index:9;background:#ffffff;border-bottom:1px solid var(--bd)}
nav .wrap{display:flex;flex-wrap:wrap;gap:2px;padding:7px 28px;align-items:center}
nav a{color:var(--mu);text-decoration:none;font-size:15px;padding:4px 11px;border-radius:8px}
nav a:hover{background:var(--bg);color:var(--tx)}
nav b{font-size:15px;margin-right:12px;color:var(--tx)}
header{padding:30px 0 6px}
.tag{color:var(--ac);font-weight:700;font-size:15px;letter-spacing:.07em;text-transform:uppercase}
h1{font-size:46px;line-height:1.08;margin:8px 0 10px;letter-spacing:-.025em;font-weight:800}
h1 .w{color:var(--w)}h1 .m{color:var(--m)}
.lead{color:var(--mu);font-size:19px;max-width:900px;margin:0}
.links{margin:16px 0 0;display:flex;flex-wrap:wrap;gap:9px}
.links a{display:inline-block;padding:8px 16px;border:1px solid var(--bd);border-radius:9px;
background:var(--card);color:var(--tx);text-decoration:none;font-size:16px;font-weight:600}
.links a.on{background:var(--ac);border-color:var(--ac);color:#ffffff}
section{padding:22px 0 26px;border-top:1px solid var(--bd);scroll-margin-top:52px}
.cab{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:4px}
h2{font-size:34px;margin:0;letter-spacing:-.015em;font-weight:800;display:flex;
align-items:center;gap:12px}
h2 .n{display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;
border-radius:11px;background:var(--ac);color:#ffffff;font-size:22px;flex:none}
.quem{background:#ede9fe;color:var(--ac);font-weight:700;font-size:15px;padding:4px 13px;
border-radius:999px;white-space:nowrap}
.leg{color:var(--mu);font-size:17px;margin:0 0 14px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:18px 20px}
.g2c{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.g32{display:grid;grid-template-columns:1.2fr 1fr;gap:16px}
h3{font-size:19px;margin:0 0 10px;font-weight:700}
p{margin:0 0 9px}
ul{margin:6px 0 0;padding-left:20px}li{margin-bottom:5px}

/* faixa de indicadores: o que o olho pega primeiro em cada seção */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;
margin:0 0 16px}
.tile{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px 16px;
display:flex;flex-direction:column;justify-content:space-between;min-height:116px}
.tile .rot{color:var(--mu);font-size:14px;font-weight:600;text-transform:uppercase;
letter-spacing:.04em;line-height:1.3}
.tile b{font-size:40px;line-height:1.02;letter-spacing:-.03em;margin:6px 0 2px;font-weight:800}
.tile .vs{color:var(--mu);font-size:14px}
.tile.w{border-left:5px solid var(--w)}.tile.w b{color:var(--w)}
.tile.m{border-left:5px solid var(--m)}.tile.m b{color:var(--m)}
.tile.ok{border-left:5px solid var(--ok)}.tile.ok b{color:var(--ok)}
.tile.al{border-left:5px solid var(--al)}.tile.al b{color:var(--al)}
.tile.ac{border-left:5px solid var(--ac)}
.duo{display:flex;align-items:baseline;gap:9px;margin:6px 0 2px;flex-wrap:wrap}
.duo i{font-style:normal;font-size:36px;font-weight:800;letter-spacing:-.03em;line-height:1.02}
.duo i.m{color:var(--m)}.duo i.w{color:var(--w)}
.duo s{text-decoration:none;color:var(--mu);font-size:22px;font-weight:600}

/* barra proporcional dentro das tabelas */
.bar{position:relative;background:#eef1f6;border-radius:6px;height:30px;min-width:120px;
display:flex;align-items:center}
.bar span{position:absolute;left:0;top:0;bottom:0;border-radius:6px;opacity:.85}
.bar em{position:relative;font-style:normal;font-weight:700;font-size:16px;padding-left:9px}

table{width:100%;border-collapse:collapse;font-size:17px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--bd);vertical-align:middle}
th{color:var(--mu);font-size:14px;text-transform:uppercase;letter-spacing:.04em;font-weight:700}
tbody tr:last-child td{border-bottom:none}
.w{color:var(--w);font-weight:700}.m{color:var(--m);font-weight:700}
.pill{display:inline-block;padding:3px 12px;border-radius:999px;font-size:15px;font-weight:700}
.pill.y{background:#dcfce7;color:#14532d}
.pill.n{background:#ffedd5;color:#7c2d12}
.pill.p{background:#fef9c3;color:#713f12}

/* a leitura do gráfico, curta: 2 a 4 frases, como o enunciado pede */
.nota{background:var(--card);border:1px solid var(--bd);border-left:5px solid var(--ac);
border-radius:0 12px 12px 0;padding:13px 18px;margin:14px 0 0;font-size:17px;color:#1f2937}
.rec{background:var(--okbg);border:2px solid var(--ok);border-radius:14px;padding:16px 20px;
margin:14px 0 0;font-size:19px}
.rec b{color:var(--ok)}
.svgbox{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:10px}

.perg{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:12px}
.q{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:13px 15px}
.q .cabq{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.q .num{background:var(--ac);color:#ffffff;border-radius:7px;width:30px;height:30px;
display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:16px;
flex:none}
.q .dono{font-size:13px;font-weight:700;color:var(--ac);background:#ede9fe;padding:2px 9px;
border-radius:999px}
.q h4{margin:0 0 6px;font-size:16px;line-height:1.3;font-weight:700}
.q p{font-size:15px;line-height:1.45;color:#334155;margin:0}
footer{padding:22px 0 44px;color:var(--mu);font-size:15px;border-top:1px solid var(--bd)}
code{background:#eef1f6;padding:2px 6px;border-radius:5px;font-size:.88em}
@media(max-width:1150px){.g2c,.g32{grid-template-columns:1fr}h1{font-size:34px}h2{font-size:27px}}
"""


SECOES = (("1", "Cenário"), ("2", "Os dados"), ("3", "Como os testes funcionam"),
          ("4", "Erro tipo I"), ("5", "Poder"), ("6", "Dados reais"),
          ("7", "Conclusão"), ("8", "Perguntas"))



def perguntas(d) -> list[tuple[int, str, str, str]]:
    """As 15 perguntas da seção 5 do enunciado, quem responde e a resposta curta.

    Os números das respostas saem dos mesmos arquivos que alimentam os gráficos, então
    uma resposta nunca fica fora de sincronia com o gráfico que está logo acima dela.
    """
    t, g2 = d["taxas"], d["info_g2"]
    nos_reais = d["nos_reais"].set_index("teste")
    welch, mw = nos_reais.loc["Welch"], nos_reais.loc["Mann-Whitney"]
    desc = d["descritivas"].set_index("grupo")
    estrito = d["estrito"]

    # erro tipo I e poder, por situação e razão, já formatados
    etI = {s: {teste: taxa(t, s, 1.0, teste) for teste in COR}
           for s in resultados.situacoes(t)}
    mw_h0 = [v["Mann-Whitney"] for v in etI.values() if v["Mann-Whitney"] is not None]
    poder = {(s, r, teste): taxa(t, s, r, teste)
             for s in resultados.situacoes(t) for r in (0.8, 0.6, 0.2) for teste in COR}
    vantagem_08 = (poder[("real", 0.8, "Mann-Whitney")] - poder[("real", 0.8, "Welch")]) * 100
    vantagem_02 = (poder[("real", 0.2, "Mann-Whitney")] - poder[("real", 0.2, "Welch")]) * 100
    assim_sem = num(float(desc.loc["sem_bot", "assimetria"]))
    assim_com = num(float(desc.loc["com_bot", "assimetria"]))
    delta_mw = vg(f"{float(mw['efeito']):+.2f}")
    razao_obs = num(float(d["cenario"]["razao_medianas_observada"]), 2)
    p_welch_ex = vg(format(g2["p_t"], ".4f"))
    p_mw_ex = vg(format(g2["p_z"], ".4f"))

    itens = [
        (1,
         "Qual é o cenário de vocês e o que H₀ e H₁ afirmam, em palavras simples?",
         "Comparamos o tempo até o merge de pull requests que receberam a revisão automática "
         "de um bot com o de PRs que não receberam, no repositório "
         "<code>ant-design/ant-design</code>. H₀ diz que os dois grupos têm a mesma "
         "distribuição de tempo, ou seja, que o bot não muda nada; H₁ diz que o tempo é "
         "diferente, para mais ou para menos."),
        (2,
         "O teste de vocês é unicaudal ou bicaudal? Por quê?",
         "Bicaudal, com α = 0,05. O bot pode acelerar o merge, porque dá retorno na hora, ou "
         "atrasá-lo, porque gera mais comentários e mais rodadas de correção, e os dois "
         "resultados interessam ao projeto. Não havia razão para fixar a direção antes de "
         "olhar os dados."),
        (3,
         "Como os dados reais foram coletados, e o que eles mostraram sobre a forma da "
         "distribuição?",
         "Pela API de busca do GitHub, com <code>src/coletar_dados_reais.py</code>: PRs "
         "criados entre julho e outubro de 2026 e já mesclados, separados por o bot ter ou "
         "não comentado, e 30 sorteados de cada grupo com semente 42. A forma é muito "
         f"assimétrica: assimetria {assim_sem} e {assim_com}, cinco outliers de Tukey em "
         "cada grupo e média muito acima da mediana. O Shapiro-Wilk rejeita normalidade nos "
         "dois grupos (p &lt; 0,001)."),
        (4,
         "Como os dados reais ajudaram a escolher os parâmetros da simulação?",
         "Ajustamos uma lognormal a cada grupo em escala log: o μ e o σ do "
         "<code>config/cenario.yaml</code> são a média e o desvio dos logs dos dados reais. "
         "Escolhemos a lognormal porque o tempo é sempre positivo, tem cauda longa à direita "
         "e, em escala log, o grupo sem bot fica compatível com uma normal (p = 0,91). Dos "
         "dados reais vieram também o n = 30 por grupo e a razão entre as medianas "
         f"observada, de cerca de {razao_obs}."),
        (5,
         "O que cada um dos dois testes compara de fato (médias, postos, proporções)?",
         "O t de Welch compara as <b>médias</b> dos dois grupos, dividindo a diferença por um "
         "erro padrão que não supõe variâncias iguais. O Mann-Whitney compara <b>postos</b>: "
         "estima a probabilidade de um PR sorteado de um grupo demorar mais que um do outro, "
         "olhando só a ordem dos valores, nunca o valor em si."),
        (6,
         "No G2: o que é a distribuição da estatística sob H₀, e por que a região de rejeição "
         "fica onde fica?",
         "É a distribuição que a estatística teria se H₀ fosse verdadeira: uma t de Student "
         f"com gl ≈ {num(g2['gl'])} para o Welch e a normal padrão para o U padronizado do "
         "Mann-Whitney. A região de rejeição fica nas duas pontas porque ali estão os valores "
         "mais improváveis sob H₀, com 2,5% de cada lado para somar os 5% do teste bicaudal: "
         f"isso dá |t| ≥ {num(g2['crit_t'], 2)} e |z| ≥ {num(g2['crit_z'], 2)}."),
        (7,
         "O que significa o p-valor do exemplo mostrado no G2? E o que ele não significa?",
         "É a área das duas pontas a partir do valor observado: a chance de, sob H₀, ver uma "
         f"estatística tão extrema quanto a que vimos. No exemplo deu {p_welch_ex} no Welch e "
         f"{p_mw_ex} no Mann-Whitney. Ele <b>não</b> é a "
         "probabilidade de H₀ ser verdadeira, nem o tamanho do efeito: um p-valor pequeno diz "
         "que o resultado é improvável sob H₀, e não que a diferença seja grande ou "
         "importante na prática."),
        (8,
         "No cenário de vocês, o que seria um erro tipo I e um erro tipo II? Qual dos dois "
         "seria mais grave?",
         "Erro tipo I seria concluir que o bot muda o tempo até o merge quando ele não muda, "
         "e o projeto adotaria uma ferramenta sem benefício real. Erro tipo II seria não "
         "perceber um ganho que existe, e o projeto deixaria de lado algo que ajuda. Para "
         "quem está decidindo se adota o bot, o tipo I tende a ser mais caro, porque custa "
         "configuração e revisão extra sem retorno, mas isso depende do custo do bot no "
         "projeto."),
        (9,
         "No G3, algum teste se afastou de 5%? Ele ficou liberal ou conservador, e por quê?",
         f"O Mann-Whitney ficou entre {pct(min(mw_h0))} e {pct(max(mw_h0))} nas quatro "
         "situações, dentro da margem da simulação. Quem se afastou foi o <b>Welch, e para "
         f"menos</b>: {pct(etI['real']['Welch'], 2)} no cenário real e "
         f"{pct(etI['n_pequeno']['Welch'], 2)} com n = 10, ou seja, ele é "
         "<b>conservador</b>. Com σ ≈ 2,4 na escala log, poucos valores enormes inflam o "
         "desvio padrão estimado e o t quase nunca alcança o valor crítico. Nenhum dos dois "
         "ficou liberal."),
        (10,
         "No G4, qual teste tem mais poder? A diferença entre eles muda conforme o tamanho do "
         "efeito?",
         "O Mann-Whitney, em todas as situações com assimetria ou outliers, e a diferença "
         f"<b>cresce com o efeito</b>: no cenário real ela vai de {num(vantagem_08, 0)} "
         f"pontos na razão 0,8 para {num(vantagem_02, 0)} pontos na razão 0,2 "
         f"({pct(poder[('real', 0.2, 'Mann-Whitney')])} contra "
         f"{pct(poder[('real', 0.2, 'Welch')])}). Com dados bem comportados os dois empatam, "
         "e aí a vantagem desaparece."),
        (11,
         "Que violação de pressuposto vocês simularam, e por que ela afeta mais um teste do "
         "que o outro?",
         "Simulamos três: assimetria extrema, que é o próprio cenário real com σ ≈ 2,4; "
         "amostra pequena, com n = 10; e outliers, contaminando 10% dos valores de uma base "
         "bem comportada com um fator 10. Elas atingem o Welch porque ele depende da média e "
         "da variância, e um único valor enorme move as duas; o Mann-Whitney usa só a ordem, "
         "então um outlier pesa como qualquer outro ponto. Com outliers e razão 0,6 isso dá "
         f"{pct(poder[('outliers', 0.6, 'Mann-Whitney')])} contra "
         f"{pct(poder[('outliers', 0.6, 'Welch')])}."),
        (12,
         "Se vocês usassem α = 0,01 em vez de 0,05, o que mudaria no G3 e no G4?",
         "No G3 as barras cairiam e a linha de referência passaria a ser 1%: no cenário real "
         f"o erro tipo I iria de {pct(etI['real']['Welch'], 2)} para "
         f"{pct(estrito[1.0]['Welch'], 2)} no Welch e de "
         f"{pct(etI['real']['Mann-Whitney'], 2)} para {pct(estrito[1.0]['Mann-Whitney'], 2)} "
         "no Mann-Whitney. No G4 as curvas desceriam junto: na razão 0,2 o poder cai de "
         f"{pct(poder[('real', 0.2, 'Welch')])} para {pct(estrito[0.2]['Welch'])} no Welch e "
         f"de {pct(poder[('real', 0.2, 'Mann-Whitney')])} para "
         f"{pct(estrito[0.2]['Mann-Whitney'])} no Mann-Whitney. É a troca de sempre: menos "
         "alarme falso, menos poder."),
        (13,
         "A simulação confirmou o que o grupo esperava antes de simular? Se não, o que "
         "explica a diferença?",
         "Em duas das três expectativas, sim: o Mann-Whitney teve mais poder em dados "
         "assimétricos, e a vantagem desapareceu com dados bem comportados. A terceira só em "
         "parte: esperávamos os dois perto de 5% sem efeito, e o Welch ficou bem abaixo, em "
         f"{pct(etI['real']['Welch'], 2)}. A explicação é a mesma cauda pesada que lhe tira o "
         "poder, inflando o desvio padrão estimado."),
        (14,
         "Nos dados reais, os dois testes chegaram à mesma conclusão? O tamanho do efeito tem "
         "importância prática?",
         f"Não: o Welch não rejeita H₀ ({p_valor(float(welch['p_valor']))}) e o Mann-Whitney "
         f"rejeita ({p_valor(float(mw['p_valor']))}), exatamente o desencontro que a "
         "simulação previa para dados com essa cauda. O efeito tem importância prática: a "
         f"mediana vai de {num(float(welch['mediana_sem_bot_h']))} h sem bot para "
         f"{num(float(welch['mediana_com_bot_h']))} h com bot, e o delta de Cliff de "
         f"{delta_mw} ({mw['interpretacao_efeito']}) diz que o PR sem bot demora mais na "
         "maioria das comparações. Mas é associação, não causa: o bot não foi sorteado entre "
         "os PRs."),
        (15,
         "Qual teste vocês recomendam para o cenário, em que situação mudariam a recomendação, "
         "e qual é a principal limitação do estudo?",
         "Recomendamos o <b>Mann-Whitney</b> para tempos de merge: manteve o erro tipo I perto "
         "de 5% em todas as situações e teve muito mais poder sob assimetria e outliers. "
         "Mudaríamos se os dados fossem simétricos e sem outliers, onde os dois empatam e o "
         "Welch fica um pouco à frente, ou se a pergunta fosse sobre a média, como o total de "
         "horas gastas. A principal limitação é que o estudo é observacional: um repositório, "
         "uma janela de quatro meses, 30 PRs por grupo e nenhuma aleatorização do bot."),
    ]
    return [(n, RESPONDE[n], texto, resposta) for n, texto, resposta in itens]


# ---------------------------------------------------------------- a página inteira

def pagina(d) -> str:
    c, t, g2 = d["cenario"], d["taxas"], d["info_g2"]
    desc = d["descritivas"].set_index("grupo")
    nos_reais = d["nos_reais"].set_index("teste")
    welch_r, mw_r = nos_reais.loc["Welch"], nos_reais.loc["Mann-Whitney"]
    CINZA_SEM, VERDE_COM = COR_GRUPO["sem_bot"], COR_GRUPO["com_bot"]

    def q(situacao, razao, teste):
        return taxa(t, situacao, razao, teste)

    etI = {s: {teste: q(s, 1.0, teste) for teste in COR} for s in resultados.situacoes(t)}
    mw_h0 = [v["Mann-Whitney"] for v in etI.values() if v["Mann-Whitney"] is not None]
    med_sem = float(welch_r["mediana_sem_bot_h"])
    med_com = float(welch_r["mediana_com_bot_h"])
    p_w, p_m = float(welch_r["p_valor"]), float(mw_r["p_valor"])

    # ---------------------------------------------------------------- cabeçalho
    nav = '<nav><div class="wrap"><b>LAB04</b>' + "".join(
        f'<a href="#s{i}">{i}. {nome}</a>' for i, nome in SECOES) + "</div></nav>"

    cabecalho = (
        '<header><div class="tag">Laboratório de Experimentação de Software · LAB04 · '
        'par P1</div>'
        '<h1>O tempo até o merge de PRs muda com um bot de revisão?<br>'
        '<span class="w">t de Welch</span> × <span class="m">Mann-Whitney</span></h1>'
        f'<p class="lead">{milhar(N_REP)} repetições por situação para medir quantas vezes '
        f'cada teste acerta, e os dois testes aplicados a {len(d["reais"])} pull requests '
        'reais do <code>ant-design/ant-design</code>.</p>'
        f'<div class="links"><a href="{REPOSITORIO}">Repositório</a>'
        f'<a href="{PROJECTS}">GitHub Projects</a>'
        f'<a class="on" href="{DASHBOARD}">Dashboard</a></div></header>')

    # ---------------------------------------------------- resumo dos resultados
    resumo_kpis = _kpis(
        _duo("Poder no efeito que medimos", pct(q("real", 0.2, "Mann-Whitney")), "m",
             pct(q("real", 0.2, "Welch")), "w", "razão de medianas 0,2, cenário real"),
        _duo("Erro tipo I sem efeito", pct(q("real", 1.0, "Mann-Whitney"), 2), "m",
             pct(q("real", 1.0, "Welch"), 2), "w", "o esperado é 5,00%"),
        _duo("Poder com outliers", pct(q("outliers", 0.6, "Mann-Whitney")), "m",
             pct(q("outliers", 0.6, "Welch")), "w", "razão 0,6"),
        _duo(f"p-valor nos {len(d['reais'])} PRs reais", vg(f"{p_m:.3f}"), "m",
             vg(f"{p_w:.3f}"), "w", "rejeita H₀ × não rejeita H₀"))

    linhas_resumo = [
        ("Erro tipo I no cenário real", "o esperado é 5%",
         _barra(q("real", 1.0, "Welch"), COR["Welch"], 0.08),
         _barra(q("real", 1.0, "Mann-Whitney"), COR["Mann-Whitney"], 0.08)),
        ("Poder no cenário real", "razão de medianas 0,2",
         _barra(q("real", 0.2, "Welch"), COR["Welch"]),
         _barra(q("real", 0.2, "Mann-Whitney"), COR["Mann-Whitney"])),
        ("Poder com outliers", "razão de medianas 0,6",
         _barra(q("outliers", 0.6, "Welch"), COR["Welch"]),
         _barra(q("outliers", 0.6, "Mann-Whitney"), COR["Mann-Whitney"])),
        ("Poder com dados bem comportados", "razão de medianas 0,8",
         _barra(q("bem_comportada", 0.8, "Welch"), COR["Welch"]),
         _barra(q("bem_comportada", 0.8, "Mann-Whitney"), COR["Mann-Whitney"])),
    ]
    resumo = _tabela(
        ("Medida", "", "t de Welch", "Mann-Whitney"),
        [(nome, f'<span style="color:var(--mu);font-size:15px">{detalhe}</span>', bw, bm)
         for nome, detalhe, bw, bm in linhas_resumo]
        + [(f"Nos {len(d['reais'])} PRs reais",
            '<span style="color:var(--mu);font-size:15px">dados coletados</span>',
            f'{_pill("não rejeita H₀", "n")} <span style="color:var(--mu)">'
            f'{p_valor(p_w)}</span>',
            f'{_pill("rejeita H₀", "y")} <span style="color:var(--mu)">'
            f'{p_valor(p_m)}</span>')])

    secao_resumo = (
        '<section id="s0"><div class="cab"><h2>Resumo dos resultados</h2>'
        '<span class="quem">apresenta: Santana</span></div>'
        + resumo_kpis + '<div class="card">' + resumo
        + '<p style="margin:10px 0 0;color:var(--mu);font-size:15px">As barras de erro tipo I '
          'estão na escala de 0 a 8%; as de poder, de 0 a 100%.</p></div>'
        + '<div class="rec"><b>Recomendação: Mann-Whitney.</b> Único a manter o erro tipo I '
          'perto de 5% nas quatro situações, e com muito mais poder quando os dados são '
          'assimétricos ou têm outliers, que é o caso dos tempos de merge.</div></section>')

    # ------------------------------------------------------------- 1. cenário
    parametros = _tabela(
        ("Grupo", "Distribuição", "μ (log)", "σ (log)", "Mediana"),
        [(nome.replace("_", " "), p["distribuicao"], num(p["mu"], 3), num(p["sigma"], 3),
          num(p["mediana"], 1) + " h") for nome, p in c["grupos"].items()])
    s1 = _secao(
        "1", 1, "Cenário", "A pergunta, as hipóteses e de onde saíram os parâmetros.",
        _kpis(
            _tile("PRs reais coletados", str(len(d["reais"])), "ac",
                  f"{c['n_por_grupo']} por grupo, API do GitHub"),
            _tile("Nível de significância", f"α = {pct(ALFA, 0)}", "ac",
                  "teste bicaudal, as duas direções"),
            _tile("Repetições por situação", milhar(N_REP), "ac",
                  "margem de ±" + vg(f"{MARGEM * 100:.1f}") + " p.p."),
            _tile("Razão de medianas observada",
                  num(float(c["razao_medianas_observada"]), 2), "ac",
                  "com bot ÷ sem bot, nos dados reais")),
        '<div class="g32"><div class="card">'
        "<p><b>Pergunta.</b> O tempo até o merge de um PR é diferente quando ele recebe a "
        "revisão automática de um bot?</p>"
        "<p><b>H₀:</b> os dois grupos têm a mesma distribuição de tempo até o merge.<br>"
        "<b>H₁:</b> o tempo é diferente.</p>"
        "<p><b>Bicaudal</b> porque o bot tanto pode acelerar o merge, dando retorno na hora, "
        "quanto atrasá-lo, gerando mais rodadas de correção.</p>"
        f"<p><b>Fonte.</b> <code>{c['fonte']['repositorio']}</code>, bot "
        f"<code>{c['fonte']['bot']}</code>, PRs criados de julho a outubro de 2026 e já "
        f"mesclados, {c['n_por_grupo']} sorteados por grupo com semente {c['semente']}.</p>"
        "</div>"
        '<div class="card"><h3>Parâmetros da simulação</h3>' + parametros
        + '<p style="margin-top:12px;color:var(--mu);font-size:15px">O efeito entra como '
          "μ<sub>com bot</sub> = μ<sub>sem bot</sub> + ln(razão), com o mesmo σ. Razão = 1,0 "
          "é H₀ verdadeira; as simuladas são "
        + " · ".join(vg(f"{r:.1f}") for r in c["efeitos_razao_medianas"]) + ".</p>"
          "</div></div>")

    # -------------------------------------------------------------- 2. G1
    estat = _tabela(
        ("Grupo", "Mediana", "Q1 a Q3", "Média", "Máximo", "Assimetria", "Outliers"),
        [(g.replace("_", " "), num(float(desc.loc[g, "mediana"])) + " h",
          num(float(desc.loc[g, "q1"])) + " a " + num(float(desc.loc[g, "q3"])) + " h",
          num(float(desc.loc[g, "media"])) + " h",
          milhar(int(round(float(desc.loc[g, "maximo"])))) + " h",
          num(float(desc.loc[g, "assimetria"])),
          str(int(float(desc.loc[g, "n_outliers_tukey"]))))
         for g in ("sem_bot", "com_bot")])
    media_sem = float(desc.loc["sem_bot", "media"])
    s2 = _secao(
        "2", 2, "Os dados", "G1: o histograma de cada grupo, os reais em cima e os "
        "simulados embaixo.",
        _kpis(
            _duo("Mediana do tempo até o merge", num(med_sem) + " h", "", num(med_com) + " h",
                 "", "sem bot × com bot", CINZA_SEM, VERDE_COM),
            _tile("Assimetria dos dois grupos",
                  num(float(desc.loc["sem_bot", "assimetria"])) + " e "
                  + num(float(desc.loc["com_bot", "assimetria"])), "al",
                  "cauda longa à direita"),
            _tile("Outliers de Tukey",
                  f"{int(float(desc.loc['sem_bot', 'n_outliers_tukey']))} + "
                  f"{int(float(desc.loc['com_bot', 'n_outliers_tukey']))}", "al",
                  "em 30 PRs de cada grupo"),
            _tile("Média contra mediana", num(media_sem) + " h", "al",
                  f"contra {num(med_sem)} h de mediana, sem bot")),
        f'<div class="svgbox">{d["g1"]}</div>'
        + '<div class="card" style="margin-top:14px">' + estat + "</div>"
        + _nota(
            "Os dois grupos têm a mesma forma: uma massa de PRs rápidos e uma cauda que vai "
            "a centenas de horas. A média fica muito acima da mediana e cada grupo tem cinco "
            "outliers, então simulamos com uma <b>lognormal ajustada aos dados reais</b>, e a "
            "linha de baixo reproduz essa assimetria. É ela que vai separar os dois testes."))

    # -------------------------------------------------------------- 3. G2
    exemplo = _tabela(
        ("Teste", "Estatística", "p-valor", "Tamanho do efeito", "Decisão a 5%"),
        [('<span class="w">t de Welch</span>', "t = " + num(g2["t"], 2),
          vg(f'{g2["p_t"]:.4f}'),
          "d de Cohen = " + num(d["exemplo"][0]["efeito"], 2)
          + f' ({interpretar_efeito("d de Cohen", d["exemplo"][0]["efeito"])})',
          _pill("rejeita H₀", "y")),
         ('<span class="m">Mann-Whitney</span>', "U = " + num(g2["u"], 0)
          + ", z = " + num(g2["z"], 2), vg(f'{g2["p_z"]:.4f}'),
          "delta de Cliff = " + num(d["exemplo"][1]["efeito"], 2)
          + f' ({interpretar_efeito("delta de Cliff", d["exemplo"][1]["efeito"])})',
          _pill("rejeita H₀", "y"))])
    s3 = _secao(
        "3", 3, "Como os testes funcionam",
        "G2: a estatística de cada teste sob H₀, a região de rejeição sombreada e o p-valor "
        "do exemplo marcado como área.",
        _kpis(
            _tile("t de Welch no exemplo", "t = " + num(g2["t"], 2), "w",
                  "p-valor = " + vg(f'{g2["p_t"]:.4f}')),
            _tile("Mann-Whitney no exemplo", "z = " + num(g2["z"], 2), "m",
                  "p-valor = " + vg(f'{g2["p_z"]:.4f}')),
            _tile("Evidência do Mann-Whitney", num(g2["p_t"] / g2["p_z"], 0) + "×", "ok",
                  "mais forte que a do Welch"),
            _tile("Valor crítico (α = 5%)", "|t| ≥ " + num(g2["crit_t"], 2), "ac",
                  "e |z| ≥ " + num(g2["crit_z"], 2) + ", 2,5% em cada ponta")),
        f'<div class="svgbox">{d["g2"]}</div>'
        + '<div class="card" style="margin-top:14px">' + exemplo + "</div>"
        + _nota(
            "Cada painel mostra onde a estatística cairia se H₀ fosse verdadeira. A faixa "
            "vermelha das duas pontas é a região de rejeição e a área colorida a partir do "
            "valor observado é o p-valor: quanto menor, mais improvável o resultado sob H₀. "
            "Neste conjunto os dois rejeitam H₀, mas o p do Mann-Whitney é cerca de "
            f"{num(g2['p_t'] / g2['p_z'], 0)} vezes menor, porque a cauda longa infla o erro "
            "padrão que o Welch usa."))

    # -------------------------------------------------------------- 4. G3
    s4 = _secao(
        "4", 4, "Erro tipo I",
        "G3: proporção de rejeições quando H₀ é verdadeira, em cada situação simulada.",
        _kpis(
            _duo("Cenário real", pct(etI["real"]["Mann-Whitney"], 2), "m",
                 pct(etI["real"]["Welch"], 2), "w", "o esperado é 5,00%"),
            _tile("Mann-Whitney nas 4 situações",
                  pct(min(mw_h0)) + " a " + pct(max(mw_h0)), "ok", "sempre dentro da margem"),
            _tile("Pior caso do Welch", pct(etI["n_pequeno"]["Welch"], 2), "al",
                  "com n = 10, seis vezes abaixo de 5%"),
            _tile("Welch com dados bem comportados", pct(etI["bem_comportada"]["Welch"], 2),
                  "ok", "aqui ele acerta o alvo")),
        f'<div class="svgbox">{d["g3"]}</div>'
        + _nota(
            "Os dois grupos foram gerados com a mesma distribuição, então toda rejeição aqui "
            "é erro tipo I. O <b>Mann-Whitney ficou perto de 5% nas quatro situações</b> e "
            "quem se desviou foi o <b>Welch, sempre para baixo</b>: ele é conservador quando "
            "os dados são muito assimétricos, porque poucos valores enormes inflam o desvio "
            "padrão estimado. <b>Nenhum dos dois é liberal</b>, e ser conservador tem preço: "
            "aparece no poder, na seção seguinte."))

    # -------------------------------------------------------------- 5. G4
    s5 = _secao(
        "5", 5, "Poder",
        "G4: com que frequência cada teste detecta o efeito, por razão entre as medianas "
        "(1,0 = sem efeito, 0,2 = efeito grande).",
        _kpis(
            _duo("Cenário real, razão 0,2", pct(q("real", 0.2, "Mann-Whitney")), "m",
                 pct(q("real", 0.2, "Welch")), "w", "a vantagem é do Mann-Whitney"),
            _duo("Com outliers, razão 0,6", pct(q("outliers", 0.6, "Mann-Whitney")), "m",
                 pct(q("outliers", 0.6, "Welch")), "w", "a maior diferença de todas"),
            _duo("Bem comportada, razão 0,8", pct(q("bem_comportada", 0.8, "Mann-Whitney")),
                 "m", pct(q("bem_comportada", 0.8, "Welch")), "w",
                 "empate: aqui a vantagem some"),
            _tile("Poder de 80% no cenário real", "nenhum", "al",
                  f"com {c['n_por_grupo']} PRs por grupo")),
        f'<div class="svgbox">{d["g4"]}</div>'
        + _nota(
            "Agora o efeito existe, e a pergunta é quantas vezes cada teste o encontra. O "
            "<b>Mann-Whitney ganha no cenário real, com amostra pequena e, de longe, com "
            "outliers</b>, e a diferença cresce junto com o efeito. A vantagem <b>muda de "
            "lado só com dados bem comportados</b>, onde eles empatam e o Welch fica à frente "
            "por pouco, que é o esperado quando o pressuposto vale. Vale notar que nenhum dos "
            "dois chega a 80% de poder no cenário real."))

    # -------------------------------------------------------------- 6. dados reais
    tabela_reais = _tabela(
        ("Teste", "Estatística", "p-valor", "Tamanho do efeito", "Conclusão a 5%"),
        [(f'<span class="{"w" if teste == "Welch" else "m"}">{teste}</span>',
          ("t = " + num(float(linha["estatistica"]), 2) if teste == "Welch"
           else "U = " + num(float(linha["estatistica"]), 0)),
          p_valor(float(linha["p_valor"])),
          f'{linha["nome_efeito"]} = {vg(format(float(linha["efeito"]), "+.2f"))} '
          f'({linha["interpretacao_efeito"]})',
          _pill("rejeita H₀", "y") if bool(linha["rejeita_h0"])
          else _pill("não rejeita H₀", "n"))
         for teste, linha in ((n, nos_reais.loc[n]) for n in ("Welch", "Mann-Whitney"))])
    s6 = _secao(
        "6", 6, "Dados reais",
        f"Os dois testes aplicados aos {len(d['reais'])} PRs coletados.",
        _kpis(
            _tile("t de Welch", p_valor(p_w), "w", "não rejeita H₀"),
            _tile("Mann-Whitney", p_valor(p_m), "m", "rejeita H₀"),
            _duo("Mediana observada", num(med_sem) + " h", "", num(med_com) + " h", "",
                 "sem bot × com bot", CINZA_SEM, VERDE_COM),
            _tile("Diferença entre as medianas", num(med_sem - med_com) + " h", "ok",
                  "mais rápido com bot, mas não é causa")),
        '<div class="card">' + tabela_reais + "</div>"
        + _nota(
            "Os <b>dois testes discordam</b>, exatamente o desencontro que a simulação previa "
            "para dados com essa cauda, e isso mostra que a escolha do teste pode mudar a "
            "resposta do estudo. Na prática a diferença é grande, de "
            f"{num(med_sem)} h para {num(med_com)} h de mediana. Mas é <b>associação, não "
            "causa</b>: o bot não foi sorteado entre os PRs, e quem o aciona pode estar "
            "escolhendo PRs mais simples."))

    # -------------------------------------------------------------- 7. conclusão
    esperado = _tabela(
        ("O que esperávamos antes de simular", "O que encontramos", ""),
        [("O Mann-Whitney teria mais poder em dados assimétricos",
          f"Confirmado em todas as situações com assimetria ou outliers: "
          f"{pct(q('real', 0.2, 'Mann-Whitney'))} contra {pct(q('real', 0.2, 'Welch'))} na "
          "razão 0,2", _pill("confirmado", "y")),
         ("Os dois ficariam perto de 5% quando não há efeito",
          f"Só o Mann-Whitney ({pct(etI['real']['Mann-Whitney'], 2)}); o Welch ficou "
          f"conservador, em {pct(etI['real']['Welch'], 2)} no cenário real e "
          f"{pct(etI['n_pequeno']['Welch'], 2)} com n = 10", _pill("em parte", "p")),
         ("A vantagem sumiria com dados bem comportados",
          f"Confirmado: {pct(q('bem_comportada', 0.8, 'Welch'))} contra "
          f"{pct(q('bem_comportada', 0.8, 'Mann-Whitney'))} na razão 0,8",
          _pill("confirmado", "y"))])
    s7 = _secao(
        "7", 7, "Conclusão", "O que o grupo esperava, o que apareceu, e o que recomendamos.",
        _kpis(
            _tile("Recomendação", "Mann-Whitney", "ok", "para tempos de merge"),
            _tile("Expectativas confirmadas", "2 de 3", "ac",
                  "a terceira só em parte: o Welch ficou conservador"),
            _tile("Mudaríamos se", "dados simétricos", "ac",
                  "sem outliers, ou pergunta sobre a média"),
            _tile("Limitação principal", "observacional", "al",
                  "o bot não foi sorteado entre os PRs")),
        '<div class="card">' + esperado + "</div>"
        + '<div class="g32" style="margin-top:14px"><div class="card">'
        + "<h3>Recomendação e quando ela mudaria</h3>"
          "<p>Para o tempo até o merge de PRs, use o <b>Mann-Whitney</b>: foi o único a "
          "manter o erro tipo I perto de 5% nas quatro situações e tem bem mais poder onde "
          "esses dados vivem, com assimetria alta e outliers.</p>"
          "<p>Mudaríamos com dados simétricos e sem outliers, onde os dois empatam e o Welch "
          "fica um pouco à frente, ou se a pergunta fosse sobre a <b>média</b> e não sobre a "
          "tendência central, como no total de horas gastas em revisão.</p></div>"
        + '<div class="card"><h3>Limitações</h3><ul>'
          "<li>Estudo <b>observacional</b>: a diferença observada não prova causa.</li>"
          "<li>Um único repositório e uma janela de quatro meses.</li>"
          f"<li>{c['n_por_grupo']} PRs por grupo: pelo G4, nem o Mann-Whitney chega a 80% de "
          "poder nesse tamanho.</li>"
          "<li>A simulação supõe lognormal; com outra forma, as taxas mudariam.</li>"
          "</ul></div></div>")

    # -------------------------------------------------------------- 8. perguntas
    lista = perguntas(d)
    cartoes = "".join(
        f'<div class="q"><div class="cabq"><span class="num">{n}</span>'
        f'<span class="dono">{quem}</span></div><h4>{p}</h4><p>{r}</p></div>'
        for n, quem, p, r in lista)
    por_pessoa = Counter(quem for _, quem, _, _ in lista)
    divisao = " · ".join(f"{quem}: {quantas}" for quem, quantas in por_pessoa.most_common())
    s8 = ('<section id="s8"><div class="cab"><h2><span class="n">8</span>Perguntas da '
          f'apresentação</h2><span class="quem">{divisao}</span></div>'
          '<p class="leg">As 15 perguntas da seção 5 do enunciado, com quem responde e a '
          'resposta curta. Tudo visível: não há nada para clicar.</p>'
          f'<div class="perg">{cartoes}</div></section>')

    rodape = (
        "<footer>Todos os números desta página são gerados por "
        "<code>python -m src.gerar_pagina</code> a partir de "
        "<code>config/cenario.yaml</code>, <code>data/</code> e "
        f"<code>resultados/*.csv</code>, com a semente {c['semente']} e {milhar(N_REP)} "
        "repetições por situação. Rodar de novo produz exatamente a mesma página. Código, "
        f'issues e histórico no <a href="{REPOSITORIO}">repositório</a>.</footer>')

    return ("<!DOCTYPE html>\n<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>LAB04 · Welch × Mann-Whitney no tempo até o merge de PRs</title>"
            "<meta name=\"description\" content=\"Comparação do t de Welch com o "
            "Mann-Whitney por simulação de Monte Carlo, no tempo até o merge de pull "
            "requests com e sem bot de revisão.\">"
            f"<style>{CSS}</style></head><body>{nav}<div class=\"wrap\">"
            + cabecalho + secao_resumo + s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + rodape
            + "</div></body></html>\n")


def main(saida: Path | str = SAIDA) -> None:
    html = pagina(carregar())
    Path(saida).write_text(html, encoding="utf-8")
    print(f"gravado {saida} ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
