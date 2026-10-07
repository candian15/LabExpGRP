import pytest

from metricas.cfr import (
    FALHA,
    SUCESSO,
    cfr_ci,
    classificar_conclusion,
    contar_ci,
    runs_validos,
)
from tests.conftest import run


@pytest.mark.parametrize(
    "conclusion, esperado",
    [
        ("success", SUCESSO),
        ("failure", FALHA),
        ("timed_out", FALHA),
        ("startup_failure", FALHA),
        ("cancelled", None),
        ("skipped", None),
        ("neutral", None),
        ("action_required", None),
        ("stale", None),
        (None, None),  # execução em andamento
        ("", None),
    ],
)
def test_classificacao_segue_tabela_do_enunciado(conclusion, esperado):
    assert classificar_conclusion(conclusion) == esperado


def test_cfr_ignora_cancelados_e_em_andamento():
    runs = [
        run("09:00", "success"),
        run("10:00", "failure"),
        run("11:00", "success"),
        run("12:00", "success"),
        run("13:00", "cancelled"),
        run("14:00", "skipped"),
        run("15:00", None),
    ]
    assert contar_ci(runs) == (1, 3)
    assert cfr_ci(runs) == pytest.approx(0.25)


def test_timed_out_e_startup_failure_contam_como_falha():
    runs = [run("09:00", "timed_out"), run("10:00", "startup_failure"), run("11:00", "success")]
    assert cfr_ci(runs) == pytest.approx(2 / 3)


def test_cfr_junta_todos_os_workflows():
    runs = [
        run("09:00", "failure", workflow_id=1),
        run("09:00", "success", workflow_id=2),
        run("10:00", "success", workflow_id=3),
        run("11:00", "success", workflow_id=3),
    ]
    assert cfr_ci(runs) == pytest.approx(0.25)


def test_cfr_sem_runs_validos_retorna_none():
    assert cfr_ci([]) is None
    assert cfr_ci([run("09:00", "cancelled"), run("10:00", "skipped")]) is None


def test_cfr_extremos():
    assert cfr_ci([run("09:00", "success")]) == 0
    assert cfr_ci([run("09:00", "failure")]) == 1


def test_runs_validos_para_filtro_de_inclusao():
    runs = [run("09:00", "success"), run("10:00", "cancelled"), run("11:00", "failure")]
    assert len(runs_validos(runs)) == 2
