"""Dashboard da S01: cenário, G1 e G2.

Roda a partir da pasta LAB04:

    streamlit run dashboard/app.py

As figuras vêm dos módulos dos outros integrantes (``src.graficos_g1.fig_g1`` e
``src.graficos.fig_g2``). Se algum ainda não estiver disponível, a seção mostra um
aviso em vez de quebrar a página — assim o esqueleto roda mesmo com a integração
pela metade.
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


def secao_indisponivel(titulo: str, erro: Exception, de_quem: str) -> None:
    """Aviso no lugar da figura, para o esqueleto rodar com a integração incompleta."""
    st.warning(
        f"**{titulo}** ainda não pôde ser gerado ({de_quem}).\n\n"
        f"Motivo: `{type(erro).__name__}: {erro}`"
    )


# ------------------------------------------------------------------- cabeçalho
st.title("Welch × Mann-Whitney: tempo até o merge de PRs")
st.caption(
    f"Laboratório de Experimentação de Software — LAB04, Sprint 01 &nbsp;·&nbsp; "
    f"[Repositório]({REPOSITORIO}) &nbsp;·&nbsp; [GitHub Projects]({PROJECTS})"
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
st.header("2. G1 — Os dados reais e os simulados")

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
Os tempos de merge são **muito assimétricos**: a mediana é de 7,7 h sem bot e 1,5 h
com bot, mas há PRs que levaram mais de 300 h, e a média de cada grupo fica bem acima
da mediana. Por isso os grupos são simulados com distribuições **lognormais** ajustadas
aos dados reais, com σ ≈ 2,4 e 2,0 na escala log. O eixo está em escala logarítmica
para que a forma de cada grupo apareça; em escala linear os outliers achatariam tudo
contra o zero. A comparação entre a linha de cima e a de baixo mostra que a simulação
reproduz a assimetria e a cauda longa observadas.
    """.strip()
)

st.divider()

# -------------------------------------------------------------------- 3. G2
st.header("3. G2 — A distribuição da estatística sob H₀")

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
Cada painel mostra a distribuição da estatística **quando H₀ é verdadeira**: a t de
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
st.caption(
    "Os números desta página são gerados na hora, a partir de `config/cenario.yaml` "
    "e da semente nele registrada. Rodar de novo produz exatamente o mesmo resultado."
)
