"""Dashboard do Lab04: as sete seções do enunciado, na ordem dele.

Esta é a versão que roda localmente. A versão publicada (GitHub Pages) é a mesma
história em uma página só, gerada por ``python -m src.gerar_pagina``.

Roda a partir da pasta LAB04:

    streamlit run dashboard/app.py

As figuras vêm de ``src.graficos_g1`` e ``src.graficos``, e os números das seções 4 e 5
saem dos CSVs de ``resultados/`` (gerados por ``python -m src.rodar_tudo``). Se um módulo
ou um CSV ainda não estiver lá, a seção mostra um aviso em vez de quebrar a página —
assim a página roda mesmo com a integração pela metade.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

REPOSITORIO = "https://github.com/candian15/LabExpGRP"
PROJECTS = "https://github.com/users/candian15/projects/2"
# O enunciado exige os três links no topo da página.
DASHBOARD = "https://candian15.github.io/LabExpGRP/"

st.set_page_config(page_title="LAB04 — Welch × Mann-Whitney", layout="wide")


# ----------------------------------------------------------------- carregamento
@st.cache_data
def carregar_cenario() -> dict:
    from src.simulacao import ler_cenario

    return ler_cenario(RAIZ / "config" / "cenario.yaml")


@st.cache_data
def carregar_reais():
    import pandas as pd

    return pd.read_csv(RAIZ / "data" / "dados_reais.csv")


@st.cache_data
def gerar_conjunto(_cenario: dict) -> dict:
    """Um conjunto simulado com a semente do cenário (o mesmo em toda a página)."""
    from src.simulacao import gerar_grupos

    return gerar_grupos(_cenario)


@st.cache_data
def carregar_taxas():
    """As taxas de rejeição das simulações (Q1, Q2 e Q3), do jeito que o G3 e o G4 leem."""
    from src import resultados

    return resultados.ler_taxas(RAIZ / "resultados")


@st.cache_data
def carregar_dados_reais():
    """Os dois testes já aplicados aos 60 PRs (``python -m src.dados_reais``)."""
    import pandas as pd

    return pd.read_csv(RAIZ / "resultados" / "dados_reais.csv")


def taxa(taxas, teste: str, razao: float = 1.0, situacao: str = "real"):
    """Uma taxa de rejeição da tabela, para escrever o número no meio do texto.

    Devolve ``None`` quando a simulação daquela linha ainda não existe, e aí o
    parágrafo que usaria o número simplesmente não aparece.
    """
    linha = taxas[(taxas["situacao"] == situacao) & (taxas["teste"] == teste)
                  & (taxas["razao"] == razao)]
    return None if linha.empty else float(linha["taxa_rejeicao"].iloc[0])


def pct(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}%}".replace(".", ",")


def secao_indisponivel(titulo: str, erro: Exception, de_quem: str) -> None:
    """Aviso no lugar da figura, para o esqueleto rodar com a integração incompleta."""
    st.warning(
        f"**{titulo}** ainda não pôde ser gerado ({de_quem}).\n\n"
        f"Motivo: `{type(erro).__name__}: {erro}`"
    )


# ------------------------------------------------------------------- cabeçalho
st.title("Welch × Mann-Whitney: tempo até o merge de PRs")
_links = [f"[Repositório]({REPOSITORIO})", f"[GitHub Projects]({PROJECTS})"]
if DASHBOARD:
    _links.insert(0, f"[Dashboard]({DASHBOARD})")
st.caption(
    "Laboratório de Experimentação de Software — LAB04 &nbsp;·&nbsp; "
    + " &nbsp;·&nbsp; ".join(_links)
)

try:
    cenario = carregar_cenario()
except Exception as e:  # noqa: BLE001 - a página precisa abrir mesmo sem o cenário
    st.error(f"Não foi possível ler `config/cenario.yaml`: {e}")
    st.stop()

st.divider()

# ------------------------------------------------------------- 1. o cenário
st.header("1. Cenário")

col_a, col_b = st.columns([3, 2])
with col_a:
    st.markdown(
        """
Queremos saber se **o tempo até o merge de um PR muda quando ele recebe a revisão
automática de um bot**. A hipótese nula (H₀) diz que os dois grupos têm a mesma
distribuição de tempo; a alternativa (H₁) diz que o tempo é diferente. O teste é
bicaudal, com α = 0,05, porque o bot tanto pode acelerar o merge, dando retorno
imediato, quanto atrasá-lo, gerando mais rodadas de correção.

Os dados reais vêm de 30 PRs com bot e 30 sem bot do repositório
`ant-design/ant-design`, criados entre julho e outubro de 2026 e coletados pela API
do GitHub. Eles servem para **ajustar os parâmetros da simulação**, não para
responder a pergunta diretamente.
        """.strip()
    )
with col_b:
    st.markdown("**Parâmetros da simulação** (`config/cenario.yaml`)")
    linhas = []
    for nome, p in cenario["grupos"].items():
        linhas.append(
            {
                "Grupo": nome.replace("_", " "),
                "Distribuição": p["distribuicao"],
                "μ (log)": round(p["mu"], 3),
                "σ (log)": round(p["sigma"], 3),
                "Mediana (h)": round(p["mediana"], 2),
            }
        )
    st.dataframe(linhas, hide_index=True, width="stretch")
    st.caption(
        f"n = {cenario['n_por_grupo']} por grupo &nbsp;·&nbsp; "
        f"semente = {cenario['semente']} &nbsp;·&nbsp; "
        f"razão de medianas observada = {cenario['razao_medianas_observada']}"
    )

st.divider()

# -------------------------------------------------------------------- 2. G1
st.header("2. Os dados")
st.caption("G1 — dados reais ao lado dos simulados")

try:
    from src.graficos_g1 import fig_g1, simular_para_g1
    import numpy as np

    reais = carregar_reais()
    simulados = simular_para_g1(cenario, np.random.default_rng(cenario["semente"]))
    st.pyplot(fig_g1(reais, simulados), width="stretch")
except Exception as e:  # noqa: BLE001
    secao_indisponivel("G1", e, "fig_g1, do Arthur")

st.markdown(
    """
Os tempos de merge são **muito assimétricos**: a mediana é de 7,7 h sem bot e 1,5 h com
bot, mas há PRs que levaram mais de 300 h, e a média de cada grupo (81 h e 21 h) fica muito
acima da mediana. Cada grupo tem 5 outliers pelo critério de Tukey, e o teste de
Shapiro-Wilk rejeita normalidade nos dois (p < 0,001).

Escolhemos a **lognormal** por três razões: o tempo é sempre positivo, a cauda é longa à
direita, e em escala log os dados reais ficam bem mais próximos de uma normal (p = 0,91 no
grupo sem bot). Os parâmetros μ e σ de cada grupo foram ajustados diretamente aos dados
reais, e não escolhidos à mão, o que faz a simulação herdar a assimetria observada em vez de
supor uma forma conveniente. O eixo está em escala logarítmica para que a forma de cada grupo
apareça; em escala linear os outliers achatariam tudo contra o zero. Comparando a linha de
cima com a de baixo dá para ver que a simulação reproduz a assimetria e a cauda longa.
    """.strip()
)

st.divider()

# -------------------------------------------------------------------- 3. G2
st.header("3. Como os testes funcionam")
st.caption("G2 — distribuição da estatística sob H₀")

grupos = gerar_conjunto(cenario)
controle, tratamento = cenario["controle"], cenario["tratamento"]
a, b = grupos[controle], grupos[tratamento]

try:
    from src.graficos import fig_g2

    st.pyplot(fig_g2(a, b), width="stretch")
except Exception as e:  # noqa: BLE001
    secao_indisponivel("G2", e, "fig_g2, do Pedro")

try:
    from src.testes import aplicar_testes

    resultados = aplicar_testes(a, b)
    st.dataframe(
        [
            {
                "Teste": r["teste"],
                "Estatística": round(r["estatistica"], 3),
                "p-valor": round(r["p_valor"], 4),
                r["nome_efeito"]: round(r["efeito"], 3),
                "Rejeita H₀ (α = 5%)": "sim" if r["rejeita_h0"] else "não",
            }
            for r in resultados
        ],
        hide_index=True,
        width="stretch",
    )
except Exception as e:  # noqa: BLE001
    secao_indisponivel("Tabela dos testes", e, "aplicar_testes, do Pedro")

st.markdown(
    """
Os dois testes respondem à mesma pergunta comparando coisas diferentes: o **Welch compara
as médias** dos dois grupos, dividindo a diferença observada por um erro padrão que não
supõe variâncias iguais; o **Mann-Whitney compara os postos**, ou seja, estima a
probabilidade de um PR sorteado de um grupo demorar mais que um do outro, sem olhar o valor
em si. Cada painel mostra a distribuição da estatística **quando H₀ é verdadeira**: a t de
Student para o Welch e a normal padrão para o U padronizado do Mann-Whitney. A área
sombreada é a região de rejeição a 5%, e a linha marca a estatística obtida neste
conjunto simulado. O p-valor é a probabilidade, sob H₀, de observar uma estatística
tão extrema quanto essa — por isso a linha cair dentro da área sombreada equivale a
p < 0,05. Como o conjunto foi gerado com medianas diferentes entre os grupos, o efeito
existe de fato, e aqui os dois testes o detectam; a S02 vai repetir isso 10.000 vezes
para medir **com que frequência** cada um acerta.
    """.strip()
)

st.divider()

# ----------------------------------------------------------------- 4 e 5: G3 e G4
# As duas seções leem a mesma tabela (Q1, Q2 e Q3), então a leitura é feita uma vez só.
try:
    from src import resultados
    from src.graficos import fig_g3, fig_g4

    taxas = carregar_taxas()
except Exception as e:  # noqa: BLE001
    taxas = None
    erro_dos_resultados = e


st.header("4. Erro tipo I")
st.caption("G3 — proporção de rejeições com H₀ verdadeira, com a linha em 5%")

if taxas is None:
    secao_indisponivel("G3", erro_dos_resultados, "as simulações da Q1 e da Q3")
else:
    try:
        st.pyplot(fig_g3(taxas), width="stretch")
    except Exception as e:  # noqa: BLE001
        secao_indisponivel("G3", e, "as simulações da Q1 e da Q3")

    welch_h0, mw_h0 = taxa(taxas, "Welch"), taxa(taxas, "Mann-Whitney")
    if None not in (welch_h0, mw_h0):
        # uma linha por situação já simulada, para o texto falar de todas elas
        h0 = {s: {teste: taxa(taxas, teste, situacao=s) for teste in ("Welch", "Mann-Whitney")}
              for s in resultados.situacoes(taxas)}
        mw_todas = [v["Mann-Whitney"] for v in h0.values() if v["Mann-Whitney"] is not None]
        faixa_mw = (f"ficou entre {pct(min(mw_todas))} e {pct(max(mw_todas))} nas "
                    f"{len(mw_todas)} situações" if len(mw_todas) > 1
                    else f"ficou em {pct(mw_h0, 2)}")
        welch_n10 = taxa(taxas, "Welch", situacao="n_pequeno")
        welch_bem = taxa(taxas, "Welch", situacao="bem_comportada")
        piores = f"{pct(welch_h0, 2)} no cenário real"
        if welch_n10 is not None:
            piores += f" e {pct(welch_n10, 2)} com n = 10"
        acerta = (f", embora acerte quando os dados são bem comportados "
                  f"({pct(welch_bem, 2)})" if welch_bem is not None else "")
        st.markdown(
            f"""
Aqui os dois grupos foram gerados com **a mesma distribuição**, então toda rejeição é erro
tipo I e o esperado é 5%. O **Mann-Whitney {faixa_mw}**, sempre dentro da margem de ±0,4
ponto percentual que a simulação tem nesse tamanho. Quem se desvia é o **Welch, e sempre
para menos**: {piores}{acerta}. Ou seja, ele é **conservador** quando os dados são muito
assimétricos, porque com σ ≈ 2,4 na escala log a média de cada grupo é dominada por poucos
valores enormes, o desvio padrão estimado fica inflado e a estatística t quase nunca
alcança o valor crítico. **Nenhum dos dois ficou liberal**, e ser conservador não sai de
graça: o preço aparece na seção seguinte, como perda de poder.
            """.strip()
        )

    faltam = [s for s in resultados.ORDEM if s not in resultados.situacoes(taxas)]
    if faltam:
        st.info(
            "Por enquanto só o cenário real. As outras situações entram quando o "
            f"`resultados/q3.csv` chegar ({', '.join(resultados.nome(s) for s in faltam)})."
        )

st.divider()

st.header("5. Poder")
st.caption("G4 — curvas de poder dos dois testes por tamanho do efeito")

if taxas is None:
    secao_indisponivel("G4", erro_dos_resultados, "as simulações da Q2 e da Q3")
else:
    try:
        st.pyplot(fig_g4(taxas), width="stretch")
    except Exception as e:  # noqa: BLE001
        secao_indisponivel("G4", e, "as simulações da Q2 e da Q3")

    menor = min(taxas["razao"])
    mw_efeito = taxa(taxas, "Mann-Whitney", menor)
    welch_efeito = taxa(taxas, "Welch", menor)
    razao_simulada = f"{menor:.1f}".replace(".", ",")
    razao_real = f"{cenario['razao_medianas_observada']:.2f}".replace(".", ",")
    if None not in (mw_efeito, welch_efeito):
        # onde a vantagem muda de lado: a comparação par a par em cada situação
        mw_n10 = taxa(taxas, "Mann-Whitney", menor, "n_pequeno")
        welch_n10 = taxa(taxas, "Welch", menor, "n_pequeno")
        mw_out = taxa(taxas, "Mann-Whitney", 0.6, "outliers")
        welch_out = taxa(taxas, "Welch", 0.6, "outliers")
        mw_bem = taxa(taxas, "Mann-Whitney", 0.8, "bem_comportada")
        welch_bem = taxa(taxas, "Welch", 0.8, "bem_comportada")
        outras = ""
        if None not in (mw_n10, welch_n10):
            outras += (f" Ganha também com **amostra pequena** ({pct(mw_n10)} contra "
                       f"{pct(welch_n10)} na mesma razão)")
        if None not in (mw_out, welch_out):
            outras += (f" e ganha de longe **com outliers** ({pct(mw_out)} contra "
                       f"{pct(welch_out)} na razão 0,6), que é a situação em que a média "
                       f"sofre e os postos não.")
        vira = ""
        if None not in (mw_bem, welch_bem):
            vira = (f" A vantagem **muda de lado só com dados bem comportados**: ali eles "
                    f"empatam e o Welch fica à frente por pouco ({pct(welch_bem)} contra "
                    f"{pct(mw_bem)} na razão 0,8), que é o esperado quando o pressuposto "
                    f"de normalidade vale.")
        st.markdown(
            f"""
Agora existe efeito de verdade, e a pergunta é com que frequência cada teste o encontra. No
maior efeito simulado (razão de medianas = {razao_simulada}, perto dos {razao_real} que
medimos nos dados reais), o **Mann-Whitney detecta em {pct(mw_efeito)}** das repetições e o
**Welch em {pct(welch_efeito)}**, e a diferença entre os dois aumenta junto com o
efeito.{outras}{vira} É o que o grupo esperava antes de simular: o Welch compara médias, e a
variância causada pelos valores extremos esconde a diferença, enquanto o Mann-Whitney
compara postos. Vale notar que **nenhum dos dois chega aos 80% de poder no cenário real**
com 30 PRs por grupo, ou seja, a amostra que coletamos seria pequena demais para garantir a
detecção mesmo do efeito que de fato observamos.
            """.strip()
        )

st.divider()

st.header("6. Dados reais")
st.caption("Os dois testes aplicados aos 60 PRs coletados")

try:
    nos_reais = carregar_dados_reais().set_index("teste")
except Exception as e:  # noqa: BLE001
    nos_reais = None
    secao_indisponivel("Tabela dos dados reais", e, "`python -m src.dados_reais`")

if nos_reais is not None:
    st.dataframe(
        [
            {
                "Teste": nome,
                "Estatística": round(float(linha["estatistica"]), 3),
                "p-valor": round(float(linha["p_valor"]), 4),
                "Tamanho do efeito": (
                    f"{linha['nome_efeito']} = {float(linha['efeito']):+.2f} "
                    f"({linha['interpretacao_efeito']})"
                ),
                "Conclusão (α = 5%)": ("rejeita H₀" if bool(linha["rejeita_h0"])
                                       else "não rejeita H₀"),
            }
            for nome, linha in ((n, nos_reais.loc[n]) for n in ("Welch", "Mann-Whitney"))
        ],
        hide_index=True,
        width="stretch",
    )

    welch_r, mw_r = nos_reais.loc["Welch"], nos_reais.loc["Mann-Whitney"]
    med_sem = float(welch_r["mediana_sem_bot_h"])
    med_com = float(welch_r["mediana_com_bot_h"])
    p_welch = f"{float(welch_r['p_valor']):.3f}".replace(".", ",")
    p_mw = f"{float(mw_r['p_valor']):.3f}".replace(".", ",")
    efeito_mw = f"{float(mw_r['efeito']):+.2f}".replace(".", ",")
    st.markdown(
        f"""
Aqui não há resposta certa conhecida: estes são os PRs de verdade, e os **dois testes
discordam**. O Welch **não rejeita H₀** (p = {p_welch}), o Mann-Whitney **rejeita**
(p = {p_mw}), e é exatamente o desencontro que a simulação previa para dados com esta
cauda: a média é arrastada por poucos PRs muito lentos e o Welch perde poder, enquanto
o Mann-Whitney olha só a ordem. Na prática a diferença é grande: a mediana vai de
**{med_sem:.1f} h sem bot para {med_com:.1f} h com bot**, e o delta de Cliff de
{efeito_mw} ({mw_r['interpretacao_efeito']}) diz que o PR sem bot demora mais na maioria
das comparações. Mas isso é **associação, não causa**: o bot não foi sorteado entre os
PRs, e quem o aciona pode estar escolhendo PRs mais simples.
        """.strip()
    )

st.divider()

st.header("7. Conclusão")
st.caption("O que o grupo esperava × o que encontrou, e qual teste recomendamos")

if taxas is None or nos_reais is None:
    st.info(
        "A conclusão depende dos resultados das simulações e dos testes nos dados "
        "reais. Rode `python -m src.rodar_tudo` para gerá-los."
    )
else:
    welch_h0 = taxa(taxas, "Welch")
    mw_h0 = taxa(taxas, "Mann-Whitney")
    welch_n10 = taxa(taxas, "Welch", situacao="n_pequeno")
    mw_forte = taxa(taxas, "Mann-Whitney", 0.2)
    welch_forte = taxa(taxas, "Welch", 0.2)
    welch_bem = taxa(taxas, "Welch", 0.8, "bem_comportada")
    mw_bem = taxa(taxas, "Mann-Whitney", 0.8, "bem_comportada")

    st.dataframe(
        [
            {
                "O que esperávamos antes de simular":
                    "O Mann-Whitney teria mais poder em dados assimétricos",
                "O que encontramos":
                    f"Confirmado em todas as situações com assimetria ou outliers: "
                    f"{pct(mw_forte)} contra {pct(welch_forte)} na razão 0,2",
                "Veredito": "confirmado",
            },
            {
                "O que esperávamos antes de simular":
                    "Os dois ficariam perto de 5% quando não há efeito",
                "O que encontramos":
                    f"Só o Mann-Whitney ({pct(mw_h0, 2)}); o Welch ficou conservador, em "
                    f"{pct(welch_h0, 2)} no cenário real e {pct(welch_n10, 2)} com n = 10",
                "Veredito": "em parte",
            },
            {
                "O que esperávamos antes de simular":
                    "A vantagem do Mann-Whitney sumiria com dados bem comportados",
                "O que encontramos":
                    f"Confirmado: {pct(welch_bem)} contra {pct(mw_bem)} na razão 0,8",
                "Veredito": "confirmado",
            },
        ],
        hide_index=True,
        width="stretch",
    )

    col_rec, col_lim = st.columns(2)
    with col_rec:
        st.markdown(
            f"""
**Recomendação: Mann-Whitney.** Para o tempo até o merge de PRs, ele foi o único a
manter o erro tipo I perto de 5% nas quatro situações e tem bem mais poder justamente
onde estes dados vivem, com assimetria alta e outliers.

**Quando mudaríamos.** Se os dados fossem simétricos e sem outliers, onde os dois
empatam e o Welch fica um pouco à frente ({pct(welch_bem)} contra {pct(mw_bem)}), ou se
a pergunta fosse sobre a **média** e não sobre a tendência central, como no total de
horas gastas em revisão.
            """.strip()
        )
    with col_lim:
        st.markdown(
            f"""
**Limitações.**

- Estudo **observacional**: o bot não foi sorteado entre os PRs, então a diferença
  observada não prova causa.
- Um único repositório e uma janela de quatro meses.
- {cenario['n_por_grupo']} PRs por grupo: pelo G4, nem o Mann-Whitney chega aos 80% de
  poder nesse tamanho.
- A simulação supõe lognormal; com outra forma, as taxas mudariam.
            """.strip()
        )

st.divider()
st.caption(
    "Os números desta página são gerados na hora, a partir de `config/cenario.yaml` "
    "e da semente nele registrada. Rodar de novo produz exatamente o mesmo resultado."
)
