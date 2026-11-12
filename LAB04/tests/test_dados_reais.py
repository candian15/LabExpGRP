import numpy as np
import pandas as pd
import pytest

from src import dados_reais as dr


def test_interpretar_efeito_nos_limites():
    assert dr.interpretar_efeito("d de Cohen", 0.1) == "desprezível"
    assert dr.interpretar_efeito("d de Cohen", -0.3) == "pequeno"
    assert dr.interpretar_efeito("d de Cohen", 0.5) == "médio"
    assert dr.interpretar_efeito("d de Cohen", 1.2) == "grande"
    assert dr.interpretar_efeito("delta de Cliff", 0.10) == "desprezível"
    assert dr.interpretar_efeito("delta de Cliff", 0.20) == "pequeno"
    assert dr.interpretar_efeito("delta de Cliff", -0.40) == "médio"
    assert dr.interpretar_efeito("delta de Cliff", 0.80) == "grande"


def r(p, efeito, rejeita, nome="delta de Cliff"):
    return {"p_valor": p, "efeito": efeito, "rejeita_h0": rejeita, "nome_efeito": nome}


def test_conclusao_quando_rejeita_diz_quem_demora_mais():
    txt = dr.conclusao(r(0.004, 0.44, True), "sem bot", "com bot")
    assert txt.startswith("Rejeita H₀ (p = 0,004)")
    assert "PRs sem bot demoram mais" in txt and "médio" in txt and "+0,44" in txt
    assert "com bot demoram mais" in dr.conclusao(r(0.004, -0.44, True), "sem bot", "com bot")


def test_conclusao_quando_nao_rejeita():
    txt = dr.conclusao(r(0.17, 0.36, False, "d de Cohen"))
    assert txt.startswith("Não rejeita H₀ (p = 0,170)") and "5%" in txt and "pequeno" in txt


def test_p_muito_pequeno_vira_menor_que():
    assert "p < 0,001" in dr.conclusao(r(0.00002, 0.9, True))


@pytest.fixture
def df():
    rng = np.random.default_rng(3)
    return pd.DataFrame({
        "grupo": ["sem_bot"] * 30 + ["com_bot"] * 30,
        "horas_ate_merge": np.concatenate([rng.lognormal(3, 0.5, 30), rng.lognormal(1, 0.5, 30)]),
    })


def test_testar_dados_reais_devolve_uma_linha_por_teste(df):
    t = dr.testar_dados_reais(df)
    assert list(t["teste"]) == ["Welch", "Mann-Whitney"]
    for coluna in ("estatistica", "p_valor", "efeito", "nome_efeito", "rejeita_h0", "conclusao"):
        assert coluna in t.columns  # as colunas que a seção 6 do dashboard precisa
    assert (t["n_sem_bot"] == 30).all() and (t["n_com_bot"] == 30).all()


def test_efeito_positivo_quando_o_controle_demora_mais(df):
    t = dr.testar_dados_reais(df)
    assert (t["efeito"] > 0.8).all() and t["rejeita_h0"].all() and t["testes_concordam"].all()
    assert (t["mediana_sem_bot_h"] > t["mediana_com_bot_h"]).all()


def test_testes_discordam_quando_so_um_rejeita():
    # dados reais do projeto: o Welch não rejeita e o Mann-Whitney rejeita (cauda longa)
    t = dr.testar_dados_reais(pd.read_csv(dr.DADOS))
    por_teste = t.set_index("teste")
    assert not por_teste.loc["Welch", "rejeita_h0"] and por_teste.loc["Mann-Whitney", "rejeita_h0"]
    assert not t["testes_concordam"].any()


def test_main_grava_o_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(dr, "SAIDA", tmp_path / "resultados" / "dados_reais.csv")
    dr.main()
    saida = pd.read_csv(tmp_path / "resultados" / "dados_reais.csv")
    assert len(saida) == 2 and saida["conclusao"].str.len().min() > 20
