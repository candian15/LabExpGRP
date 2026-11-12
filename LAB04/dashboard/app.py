"""Dashboard do Lab04: as sete seções do enunciado, na ordem dele.

Preenchidas até agora: 1 a 5 (cenário, G1, G2, G3 e G4). As seções 6 e 7 entram na
entrega final.

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
# Preencher quando o dashboard for publicado (Streamlit Community Cloud ou GitHub Pages).
# O enunciado exige os três links no topo da página.
DASHBOARD = ""

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
    "Laboratório de Experimentação de Software — LAB04, Sprint 02 &nbsp;·&nbsp; "
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
        st.markdown(
            f"""
Aqui os dois grupos foram gerados com **a mesma distribuição**, então toda rejeição é erro
tipo I e o esperado é 5%. O **Mann-Whitney rejeitou em {pct(mw_h0, 2)}** das 10.000
repetições, dentro da margem de ±0,4 ponto percentual que a simulação tem nesse tamanho;
o **Welch ficou em {pct(welch_h0, 2)}**, bem abaixo. Quem se desvia, portanto, é o Welch, e
para menos: ele é **conservador** neste cenário, porque com σ ≈ 2,4 na escala log a média de
cada grupo é dominada por poucos valores enormes, o desvio padrão estimado fica inflado e a
estatística t quase nunca alcança o valor crítico. Isso não sai de graça — o preço aparece
na seção seguinte, como perda de poder.
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
        st.markdown(
            f"""
Agora existe efeito de verdade, e a pergunta é com que frequência cada teste o encontra. No
maior efeito simulado (razão de medianas = {razao_simulada}, perto dos {razao_real} que
medimos nos dados reais), o **Mann-Whitney detecta em {pct(mw_efeito)}** das repetições e o **Welch em
{pct(welch_efeito)}** — a vantagem é do Mann-Whitney em toda a curva e aumenta junto com o
efeito. É o que o grupo esperava antes de simular: o Welch compara médias, e a variância
causada pelos outliers esconde a diferença, enquanto o Mann-Whitney compara postos e quase
não sente os valores extremos. Vale notar que **nenhum dos dois chega aos 80% de poder** com
30 PRs por grupo, ou seja, a amostra real que coletamos seria pequena demais para garantir a
detecção mesmo do efeito que de fato observamos.
            """.strip()
        )

st.divider()

st.header("6. Dados reais")
st.caption("Os dois testes aplicados aos 60 PRs coletados")
st.info("Entra na entrega final.")

st.divider()

st.header("7. Conclusão")
st.info(
    "Entra na entrega final: o que o grupo esperava antes de simular, o que encontrou, "
    "e qual teste recomendamos para este cenário."
)

st.divider()
st.caption(
    "Os números desta página são gerados na hora, a partir de `config/cenario.yaml` "
    "e da semente nele registrada. Rodar de novo produz exatamente o mesmo resultado."
)
