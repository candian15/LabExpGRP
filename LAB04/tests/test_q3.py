import numpy as np
import pandas as pd
import pytest

from src import q3, resultados

COLUNAS = ["situacao", "n", "sigma", "razao", "teste", "taxa_rejeicao"]


# ------------------------------------------------------------------ contaminação
def test_contaminar_sem_fracao_nao_mexe_nos_dados():
    A = np.random.default_rng(1).lognormal(2, 0.3, (5, 30))
    assert q3.contaminar(A, 0.0, 10.0, np.random.default_rng(2)) is A


def test_contaminar_multiplica_por_dez_so_os_valores_sorteados():
    A = np.random.default_rng(1).lognormal(2, 0.3, (200, 30))
    C = q3.contaminar(A, 0.10, 10.0, np.random.default_rng(2))
    razao = C / A
    assert set(np.round(np.unique(razao), 9)) == {1.0, 10.0}
    assert (razao == 10).mean() == pytest.approx(0.10, abs=0.02)  # 10% dos valores, em média
    assert A.shape == C.shape


def test_contaminar_e_reproduzivel():
    A = np.random.default_rng(1).lognormal(2, 0.3, (10, 30))
    a = q3.contaminar(A, 0.1, 10.0, np.random.default_rng(7))
    b = q3.contaminar(A, 0.1, 10.0, np.random.default_rng(7))
    assert np.array_equal(a, b)


def test_taxa_contaminada_sem_efeito_fica_perto_do_nominal():
    taxas = q3.taxa_rejeicao_contaminada(2.0, 0.3, 30, 1.0, np.random.default_rng(42), n_rep=3000)
    assert 0.02 < taxas["Mann-Whitney"] < 0.08
    assert taxas["Welch"] < 0.08  # com outliers o Welch tende a ficar conservador, nunca liberal


def test_outliers_derrubam_o_poder_do_welch_mais_que_o_do_mann_whitney():
    taxas = q3.taxa_rejeicao_contaminada(2.0, 0.3, 30, 0.6, np.random.default_rng(42), n_rep=2000)
    assert taxas["Mann-Whitney"] > 0.9
    assert taxas["Welch"] < taxas["Mann-Whitney"] - 0.4


# --------------------------------------------------------------------- situações
def test_simular_situacao_tem_o_formato_de_q1_e_q2():
    t = q3.simular_situacao("outliers", 2.0, 0.3, 30, [1.0, 0.8], np.random.default_rng(1),
                            n_rep=200, fracao_outliers=0.1)
    assert list(t.columns) == COLUNAS
    assert len(t) == 4 and t["taxa_rejeicao"].between(0, 1).all()
    assert set(t["teste"]) == {"Welch", "Mann-Whitney"}


CENARIO = {"semente": 42, "n_por_grupo": 30, "controle": "sem_bot",
           "grupos": {"sem_bot": {"mu": 2.0, "sigma": 2.4}},
           "efeitos_razao_medianas": [1.0, 0.8, 0.6, 0.4, 0.2]}


def test_rodar_cobre_as_tres_situacoes_prometidas_no_cenario():
    t = q3.rodar(CENARIO, n_rep=100)
    assert list(t.columns) == COLUNAS
    assert len(t) == 3 * 5 * 2
    assert list(dict.fromkeys(t["situacao"])) == ["bem_comportada", "n_pequeno", "outliers"]
    assert set(t["situacao"]) <= set(resultados.ORDEM)  # o G3 e o G4 conhecem o nome
    for _, grupo in t.groupby("situacao"):  # erro tipo I (1,0) e as 4 razões de poder
        assert sorted(set(grupo["razao"])) == sorted(CENARIO["efeitos_razao_medianas"])


def test_rodar_usa_n_e_sigma_de_cada_situacao():
    t = q3.rodar(CENARIO, n_rep=100).drop_duplicates("situacao").set_index("situacao")
    assert t.loc["bem_comportada", "sigma"] == 0.3 and t.loc["bem_comportada", "n"] == 30
    assert t.loc["n_pequeno", "n"] == 10 and t.loc["n_pequeno", "sigma"] == 2.4  # sigma do cenário real
    assert t.loc["outliers", "sigma"] == 0.3 and t.loc["outliers", "n"] == 30


def test_rodar_com_a_mesma_semente_da_o_mesmo_resultado():
    pd.testing.assert_frame_equal(q3.rodar(CENARIO, n_rep=100), q3.rodar(CENARIO, n_rep=100))


def test_acrescentar_uma_situacao_no_fim_nao_muda_as_anteriores(monkeypatch):
    base = q3.rodar(CENARIO, n_rep=100)
    monkeypatch.setitem(q3.SITUACOES, "nova", {"sigma": 1.0, "n": 20, "fracao_outliers": 0.0})
    maior = q3.rodar(CENARIO, n_rep=100)
    anteriores = maior[maior["situacao"] != "nova"].reset_index(drop=True)
    pd.testing.assert_frame_equal(base, anteriores)


# ------------------------------------------------------------- arquivo e integração
def test_main_grava_q3_csv_que_o_g3_e_o_g4_conseguem_ler(tmp_path, monkeypatch):
    rodar_de_verdade = q3.rodar
    monkeypatch.setattr(q3, "PASTA_RESULTADOS", tmp_path)
    monkeypatch.setattr(q3, "rodar", lambda: rodar_de_verdade(CENARIO, n_rep=100))
    q3.main()
    taxas = resultados.ler_taxas(tmp_path)
    assert resultados.situacoes(taxas) == ["bem_comportada", "n_pequeno", "outliers"]
    assert len(resultados.erro_tipo_i(taxas)) == 3 * 2
