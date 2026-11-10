import numpy as np

from src.monte_carlo import simular, taxa_rejeicao, taxas_de_amostras


def test_sem_efeito_taxa_perto_de_5_porcento():
    rng = np.random.default_rng(42)
    taxas = taxa_rejeicao(mu=2.0, sigma=0.5, n=30, razao=1.0, rng=rng, n_rep=4000)
    for taxa in taxas.values():
        assert 0.03 < taxa < 0.07


def test_efeito_grande_quase_sempre_rejeita():
    rng = np.random.default_rng(42)
    taxas = taxa_rejeicao(mu=2.0, sigma=0.5, n=30, razao=0.3, rng=rng, n_rep=2000)
    assert all(taxa > 0.95 for taxa in taxas.values())


def test_mesma_semente_mesmo_resultado():
    a = taxa_rejeicao(2.0, 1.0, 30, 0.6, np.random.default_rng(42), n_rep=1000)
    b = taxa_rejeicao(2.0, 1.0, 30, 0.6, np.random.default_rng(42), n_rep=1000)
    assert a == b


def test_taxas_de_amostras_iguais_nao_rejeita():
    A = np.tile(np.arange(1, 31, dtype=float), (5, 1))
    assert taxas_de_amostras(A, A.copy()) == {"Welch": 0.0, "Mann-Whitney": 0.0}


def test_simular_tem_uma_linha_por_teste_e_razao():
    tabela = simular("real", 2.0, 1.0, 30, [1.0, 0.8, 0.6, 0.4, 0.2],
                     np.random.default_rng(42), n_rep=200)
    assert len(tabela) == 10
    assert list(tabela.columns) == ["situacao", "n", "sigma", "razao", "teste", "taxa_rejeicao"]
    assert tabela["taxa_rejeicao"].between(0, 1).all()
