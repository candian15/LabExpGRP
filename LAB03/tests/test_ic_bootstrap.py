import numpy as np
import pandas as pd
import pytest

from analises import ic_bootstrap as ic


@pytest.fixture
def df():
    n = 40
    rng = np.random.default_rng(0)
    freq = np.arange(1.0, n + 1.0)
    return pd.DataFrame({
        "repo": [f"o/r{i}" for i in range(n)],
        "deployment_frequency": freq,
        "lead_time_a_horas": freq * 10,
        "lead_time_b_horas": freq * 20,
        "cfr_ci": freq / 100,                      # cresce com a frequência: rho = 1
        "cfr_entrega": rng.permutation(freq) / 100,
        "recuperacao_horas": [np.nan] * 5 + list(np.arange(1.0, n - 4.0)),
        "motivo_descarte": pd.Series([None] * n, dtype=object),
    })


@pytest.fixture
def rq7():
    # 10 repositórios: C2 difere de C1 em 3; C3 é igual a C1
    c1 = ["Elite", "High", "High", "Medium", "Medium", "Medium", "Low", "Low", "High", "Elite"]
    c2 = ["High", "Medium", "High", "Medium", "Low", "Medium", "Low", "Low", "High", "Elite"]
    return pd.DataFrame({"repo": [f"o/r{i}" for i in range(10)], "C1": c1, "C2": c2, "C3": c1})


def test_intervalo_contem_o_valor_observado(df, rq7):
    t = ic.tabela(df, rq7, "cfr_entrega", replicas=300)
    assert ((t["ic95_inf"] <= t["valor"] + 1e-9) & (t["valor"] <= t["ic95_sup"] + 1e-9)).all()


def test_mediana_ignora_vazios(df):
    t = ic.tabela(df, None, "cfr_entrega", replicas=200)
    linha = t[t["estatistica"] == "mediana Tempo de recuperação"].iloc[0]
    assert linha["valor"] == pytest.approx(df["recuperacao_horas"].median())


def test_correlacao_perfeita_tem_intervalo_degenerado(df):
    t = ic.tabela(df, None, "cfr_entrega", replicas=200)
    linha = t[t["estatistica"] == "rho frequência x CFR (a)"].iloc[0]
    assert linha["valor"] == pytest.approx(1.0)
    assert linha["ic95_inf"] == pytest.approx(1.0)


def test_mudanca_de_categoria(rq7, df):
    t = ic.tabela(df, rq7, "cfr_entrega", replicas=200).set_index("estatistica")
    assert t.loc["% que muda C1 x C2", "valor"] == pytest.approx(30.0)
    assert t.loc["% que muda C1 x C3", "valor"] == 0
    assert t.loc["% que muda C1 x C3", "ic95_sup"] == 0


def test_semente_fixa_repete_o_resultado(df, rq7):
    a = ic.tabela(df, rq7, "cfr_entrega", replicas=100)
    b = ic.tabela(df, rq7, "cfr_entrega", replicas=100)
    pd.testing.assert_frame_equal(a, b)


def test_sem_rq7_so_tem_rq1_a_rq5(df):
    t = ic.tabela(df, None, "cfr_entrega", replicas=50)
    assert set(t["rq"]) == {"RQ01", "RQ02", "RQ03", "RQ04", "RQ05"}
