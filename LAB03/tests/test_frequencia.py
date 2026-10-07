from datetime import date

import pytest

from metricas.frequencia import deployment_frequency, semanas_da_janela


def test_janela_de_12_meses_tem_cerca_de_52_semanas():
    # Valor que o enunciado usa como referência (≈ 52,1 semanas).
    assert semanas_da_janela(date(2025, 10, 1), date(2026, 9, 30)) == pytest.approx(52.1, abs=0.1)


def test_uma_release_por_semana():
    # 364 dias = 52 semanas exatas: 52 releases dão 1 por semana.
    assert deployment_frequency(52, date(2025, 1, 1), date(2025, 12, 30)) == pytest.approx(1.0)


def test_sem_releases_na_janela():
    assert deployment_frequency(0, date(2025, 1, 1), date(2025, 12, 30)) == 0.0


def test_janela_de_um_dia_conta_como_dia_inteiro():
    # A janela é inclusiva nas duas pontas: um dia = 1/7 de semana.
    assert deployment_frequency(1, date(2025, 1, 1), date(2025, 1, 1)) == pytest.approx(7.0)


def test_janela_invertida_e_erro():
    with pytest.raises(ValueError):
        semanas_da_janela(date(2026, 1, 1), date(2025, 1, 1))
