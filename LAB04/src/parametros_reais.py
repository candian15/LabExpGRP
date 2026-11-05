"""Estatísticas dos dados reais e parâmetros da simulação (item c do enunciado).

Lê ``data/dados_reais.csv`` (colunas ``grupo`` e ``horas_ate_merge``), descreve cada grupo
(mediana, IQR, assimetria, outliers, normalidade) e ajusta uma lognormal a cada um:

    mu    = média de ln(x)          (a mediana da lognormal é exp(mu))
    sigma = desvio-padrão de ln(x)

Grava ``config/cenario.yaml`` (lido pelo gerador de dados simulados) e
``data/estatisticas_descritivas.csv`` (usado no dashboard).

Convenção do efeito nas simulações (Q1 a Q3): o grupo **controle** (``sem_bot``) tem os
parâmetros reais; o grupo **tratamento** (``com_bot``) tem a mediana do controle
multiplicada por ``razao`` (``mu_tratamento = mu_controle + ln(razao)``) e o mesmo sigma.
``razao = 1`` é H0 verdadeira; ``razao = 0,2`` é quase o que se observou nos dados reais.

Uso (a partir de LAB04/):  python -m src.parametros_reais
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

GRUPOS = ("sem_bot", "com_bot")  # controle primeiro
EFEITOS_SUGERIDOS = [1.0, 0.8, 0.6, 0.4, 0.2]  # razão de medianas (tratamento / controle)
SEMENTE = 42


def descrever(valores: pd.Series) -> dict:
    """Estatísticas descritivas e de forma de um grupo (valores positivos, em horas)."""
    x = valores.dropna().astype(float)
    x = x[x > 0]
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    iqr = q3 - q1
    log = np.log(x)
    return {
        "n": int(len(x)),
        "media": float(x.mean()),
        "desvio_padrao": float(x.std(ddof=1)),
        "mediana": float(med),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(iqr),
        "minimo": float(x.min()),
        "maximo": float(x.max()),
        "assimetria": float(stats.skew(x, bias=False)),
        "n_outliers_tukey": int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum()),
        "shapiro_p_bruto": float(stats.shapiro(x).pvalue),
        "shapiro_p_log": float(stats.shapiro(log).pvalue),
        "mu_log": float(log.mean()),
        "sigma_log": float(log.std(ddof=1)),
    }


def tabela_descritiva(df: pd.DataFrame, col_valor: str = "horas_ate_merge") -> pd.DataFrame:
    linhas = {g: descrever(df.loc[df["grupo"] == g, col_valor]) for g in GRUPOS}
    return pd.DataFrame(linhas).T.rename_axis("grupo").reset_index()


def montar_cenario(tabela: pd.DataFrame, fonte: dict) -> dict:
    """Dicionário que vira ``cenario.yaml``."""
    t = tabela.set_index("grupo")
    grupos = {
        g: {
            "distribuicao": "lognormal",
            "mediana": round(float(np.exp(t.loc[g, "mu_log"])), 4),
            "mu": round(float(t.loc[g, "mu_log"]), 6),
            "sigma": round(float(t.loc[g, "sigma_log"]), 6),
        }
        for g in GRUPOS
    }
    return {
        "cenario": "Tempo até o merge de PRs com e sem bot de revisão",
        "unidade": "horas",
        "fonte": fonte,
        "semente": SEMENTE,
        "n_por_grupo": int(t["n"].min()),
        "controle": "sem_bot",
        "tratamento": "com_bot",
        "grupos": grupos,
        "razao_medianas_observada": round(grupos["com_bot"]["mediana"] / grupos["sem_bot"]["mediana"], 4),
        "efeitos_razao_medianas": EFEITOS_SUGERIDOS,
        "convencao_efeito": "tratamento: mu = mu_controle + ln(razao); mesmo sigma do controle; razao = 1 -> H0",
    }


def main(dados: str = "data/dados_reais.csv", saida_yaml: str = "config/cenario.yaml",
         saida_csv: str = "data/estatisticas_descritivas.csv") -> dict:
    df = pd.read_csv(dados)
    tabela = tabela_descritiva(df)
    fonte = {
        "repositorio": "ant-design/ant-design",
        "bot": "copilot-pull-request-reviewer",
        "janela_pr_criados": "2026-07-01..2026-10-31",
        "detalhes": "data/FONTE.md",
    }
    cenario = montar_cenario(tabela, fonte)
    Path(saida_yaml).parent.mkdir(parents=True, exist_ok=True)
    with open(saida_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(cenario, f, allow_unicode=True, sort_keys=False)
    tabela.to_csv(saida_csv, index=False)
    print(tabela.round(3).to_string(index=False))
    print(f"\nrazão de medianas observada (com_bot / sem_bot): {cenario['razao_medianas_observada']}")
    print(f"gravado {saida_yaml} e {saida_csv}")
    return cenario


if __name__ == "__main__":
    main()
