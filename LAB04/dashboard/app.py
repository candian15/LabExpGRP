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
st.info("Seção em construção.")

st.divider()

# -------------------------------------------------------------------- 2. G1
st.header("2. G1 — Os dados reais e os simulados")
st.info("Aguardando o `fig_g1`, do Arthur.")

st.divider()

# -------------------------------------------------------------------- 3. G2
st.header("3. G2 — A distribuição da estatística sob H₀")
st.info("Aguardando o `fig_g2`, do Pedro.")
