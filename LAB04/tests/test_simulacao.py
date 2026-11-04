import numpy as np

from src.simulacao import gerar_grupos, ler_cenario

CENARIO = {
    "semente": 42,
    "n_por_grupo": 30,
    "grupos": {"sem_bot": {"mu": 3.0, "sigma": 1.0}, "com_bot": {"mu": 2.6, "sigma": 1.0}},
}


def test_le_o_cenario_do_yaml():
    cenario = ler_cenario()
    assert "grupos" in cenario and "semente" in cenario


def test_gera_os_dois_grupos_com_tamanho_certo():
    grupos = gerar_grupos(CENARIO)
    assert set(grupos) == {"sem_bot", "com_bot"}
    assert all(len(g) == 30 for g in grupos.values())


def test_tempos_sao_positivos():
    grupos = gerar_grupos(CENARIO)
    assert all((g > 0).all() for g in grupos.values())


def test_mesma_semente_gera_mesmos_dados():
    a = gerar_grupos(CENARIO)
    b = gerar_grupos(CENARIO)
    assert np.array_equal(a["sem_bot"], b["sem_bot"])


def test_mediana_proxima_do_parametro():
    grupos = gerar_grupos(CENARIO, n=20000)
    assert abs(np.median(grupos["sem_bot"]) - np.exp(3.0)) < 1.0
