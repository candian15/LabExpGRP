import numpy as np

from src.graficos import fig_g2
from src.testes import aplicar_testes, mann_whitney, welch


def test_grupos_iguais_nao_rejeitam():
    a = np.arange(1, 31, dtype=float)
    for r in aplicar_testes(a, a.copy()):
        assert r["p_valor"] > 0.05
        assert not r["rejeita_h0"]


def test_grupos_bem_diferentes_rejeitam():
    rng = np.random.default_rng(42)
    a = rng.lognormal(4, 0.5, 30)
    b = rng.lognormal(2, 0.5, 30)
    assert all(r["rejeita_h0"] for r in aplicar_testes(a, b))


def test_tamanho_do_efeito():
    a = np.array([10.0, 11, 12, 13])
    b = np.array([1.0, 2, 3, 4])
    assert welch(a, b)["efeito"] > 0
    assert mann_whitney(a, b)["efeito"] == 1.0  # todo a maior que todo b


def test_fig_g2_tem_dois_paineis():
    rng = np.random.default_rng(42)
    fig = fig_g2(rng.lognormal(3, 1, 30), rng.lognormal(2.6, 1, 30))
    assert len(fig.axes) == 2
