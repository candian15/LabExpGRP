"""Funções comuns às análises da Sprint 3 (leitura do CSV e nomes de coluna)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# colunas do repositorios.csv (README do pipeline); a do CFR (b) pode variar de nome
COL_FREQUENCIA = "deployment_frequency"
COL_LEAD_A = "lead_time_a_horas"
COL_LEAD_B = "lead_time_b_horas"
COL_CFR_A = "cfr_ci"
COL_RECUPERACAO = "recuperacao_horas"
CANDIDATAS_CFR_B = ["cfr_entrega", "cfr_b", "cfrb", "cfrb_cfr"]


def achar_coluna(df: pd.DataFrame, candidatas: list[str], escolhida: str | None = None) -> str:
    """Primeira coluna existente entre as candidatas (ou a escolhida pelo usuário)."""
    if escolhida:
        if escolhida not in df.columns:
            raise SystemExit(f"coluna {escolhida!r} não existe no CSV (colunas: {list(df.columns)})")
        return escolhida
    for c in candidatas:
        if c in df.columns:
            return c
    raise SystemExit(f"nenhuma das colunas {candidatas} existe no CSV; use a opção --col-cfr-b")


def carregar_repositorios(caminho: str | Path) -> pd.DataFrame:
    """Lê o repositorios.csv e mantém só os repositórios aprovados (sem motivo de descarte)."""
    df = pd.read_csv(caminho)
    if "motivo_descarte" in df.columns:
        df = df[df["motivo_descarte"].isna() | (df["motivo_descarte"].astype(str).str.strip() == "")]
    return df.reset_index(drop=True)
