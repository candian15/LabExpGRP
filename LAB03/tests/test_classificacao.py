import pytest

from metricas.classificacao import (
    ELITE,
    HIGH,
    LOW,
    MEDIUM,
    categoria_geral,
    classificar,
    nota_cfr,
    nota_frequencia,
    nota_lead_time,
    nota_recuperacao,
)

DIA = 24
SEMANA = 7 * DIA


def test_exemplo_do_enunciado_4_3_3_1_da_high():
    # Notas (4, 3, 3, 1) -> mediana 3 -> High.
    assert categoria_geral([4, 3, 3, 1]) == HIGH
    r = classificar(
        deployment_frequency=10,      # ≥ 7/semana      -> Elite (4)
        lead_time_horas=3 * DIA,      # 1 dia a < 1 sem -> High  (3)
        cfr=0.25,                     # > 15% e ≤ 30%   -> High  (3)
        recuperacao_horas=2 * SEMANA, # ≥ 1 semana      -> Low   (1)
    )
    assert [r["nota_frequencia"], r["nota_lead_time"], r["nota_cfr"], r["nota_recuperacao"]] == [4, 3, 3, 1]
    assert (r["dora_nota"], r["dora"]) == (3, "High")


@pytest.mark.parametrize("por_semana, esperado", [
    (7, ELITE), (20, ELITE),
    (1, HIGH), (6.99, HIGH),
    (0.99, MEDIUM), (12 / 52.1, MEDIUM),   # 12 releases numa janela de 12 meses
    (0.2, LOW), (0, LOW),
])
def test_cortes_da_frequencia(por_semana, esperado):
    assert nota_frequencia(por_semana) == esperado


@pytest.mark.parametrize("horas, esperado", [
    (0, ELITE), (23.9, ELITE),
    (DIA, HIGH), (SEMANA - 1, HIGH),
    (SEMANA, MEDIUM), (30 * DIA - 1, MEDIUM),
    (30 * DIA, LOW), (90 * DIA, LOW),
])
def test_cortes_do_lead_time(horas, esperado):
    assert nota_lead_time(horas) == esperado


@pytest.mark.parametrize("fracao, esperado", [
    (0, ELITE), (0.15, ELITE),      # o corte do CFR é ≤, não <
    (0.1501, HIGH), (0.30, HIGH),
    (0.31, MEDIUM), (0.45, MEDIUM),
    (0.46, LOW), (1.0, LOW),
])
def test_cortes_do_cfr(fracao, esperado):
    assert nota_cfr(fracao) == esperado


@pytest.mark.parametrize("horas, esperado", [
    (0.5, ELITE),
    (1, HIGH), (23.9, HIGH),
    (DIA, MEDIUM), (SEMANA - 1, MEDIUM),
    (SEMANA, LOW),
])
def test_cortes_da_recuperacao(horas, esperado):
    assert nota_recuperacao(horas) == esperado


def test_mediana_par_arredonda_para_baixo():
    # (4, 4, 1, 1) -> mediana 2,5 -> Medium.
    assert categoria_geral([4, 4, 1, 1]) == MEDIUM


def test_metrica_ausente_fica_fora_da_mediana():
    r = classificar(deployment_frequency=10, lead_time_horas=None, cfr=0.5, recuperacao_horas=0.5)
    assert r["nota_lead_time"] is None
    # Sobram as notas 4, 1 e 4 -> mediana 4 -> Elite.
    assert r["dora"] == "Elite"


def test_sem_nenhuma_metrica_nao_ha_categoria():
    r = classificar()
    assert r["dora_nota"] is None and r["dora"] is None
    assert categoria_geral([None, None]) is None


def test_doze_releases_no_ano_sao_uma_por_mes():
    # O corte Medium/Low é "1 por mês". Calculado sobre a janela real de 365
    # dias, 12 releases dão 0,2301/semana, e isso não pode cair em Low.
    from datetime import date

    from metricas.frequencia import deployment_frequency

    por_semana = deployment_frequency(12, date(2025, 10, 1), date(2026, 9, 30))
    assert nota_frequencia(por_semana) == MEDIUM
    assert nota_frequencia(deployment_frequency(11, date(2025, 10, 1), date(2026, 9, 30))) == LOW
