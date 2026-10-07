from datetime import datetime, timezone

import pytest

from metricas.recuperacao import (
    Episodio,
    episodios_do_repo,
    episodios_do_workflow,
    tempo_recuperacao,
)
from tests.conftest import run


def test_exemplo_do_enunciado_1h20(exemplo_enunciado):
    eps, _ = episodios_do_workflow(exemplo_enunciado)
    assert len(eps) == 1
    assert eps[0].horas == pytest.approx(80 / 60)
    assert tempo_recuperacao(exemplo_enunciado)["mediana_horas"] == pytest.approx(80 / 60)


def test_ordem_de_entrada_nao_importa(exemplo_enunciado):
    embaralhado = list(reversed(exemplo_enunciado))
    assert tempo_recuperacao(embaralhado)["mediana_horas"] == pytest.approx(80 / 60)


def test_falha_nunca_recuperada_e_censurada():
    runs = [
        run("09:00", "success"),
        run("10:00", "failure"),
        run("11:00", "failure"),
    ]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 1
    assert r["n_censurados"] == 1
    assert r["prop_censurados"] == 1
    assert r["mediana_horas"] is None  # censurado não entra na mediana


def test_censurado_nao_entra_na_mediana_mas_conta_na_proporcao(exemplo_enunciado):
    runs = exemplo_enunciado + [
        run("12:00", "failure", fim="12:05"),  # nunca recupera
    ]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 2
    assert r["n_censurados"] == 1
    assert r["prop_censurados"] == pytest.approx(0.5)
    assert r["mediana_horas"] == pytest.approx(80 / 60)


def test_cancelled_no_meio_do_episodio_e_ignorado():
    runs = [
        run("09:00", "success", fim="09:05"),
        run("10:00", "failure", fim="10:05"),
        run("10:20", "cancelled", fim="10:21"),  # não fecha nem abre episódio
        run("10:40", "skipped", fim="10:41"),
        run("11:00", "success", fim="11:30"),
    ]
    assert tempo_recuperacao(runs)["mediana_horas"] == pytest.approx(1.5)


def test_cancelled_nao_abre_episodio():
    runs = [run("09:00", "success"), run("10:00", "cancelled"), run("11:00", "success")]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 0
    assert r["mediana_horas"] is None
    assert r["prop_censurados"] is None


def test_sucesso_de_outro_workflow_nao_fecha_episodio():
    runs = [
        run("09:00", "success", workflow_id="CI"),
        run("10:00", "failure", workflow_id="CI", fim="10:05"),
        run("10:30", "success", workflow_id="Docs", fim="10:35"),  # outro workflow
        run("12:00", "success", workflow_id="CI", fim="12:00"),
    ]
    eps, _ = episodios_do_repo(runs)
    assert len(eps) == 1
    assert eps[0].workflow_id == "CI"
    assert eps[0].horas == pytest.approx(2.0)


def test_mediana_entre_workflows_e_episodios():
    runs = [
        # workflow 1: dois episódios de 1h e 3h
        run("08:00", "success", workflow_id=1),
        run("09:00", "failure", workflow_id=1),
        run("10:00", "success", workflow_id=1, fim="10:00"),
        run("11:00", "failure", workflow_id=1),
        run("14:00", "success", workflow_id=1, fim="14:00"),
        # workflow 2: um episódio de 2h
        run("08:00", "success", workflow_id=2),
        run("09:00", "failure", workflow_id=2),
        run("11:00", "success", workflow_id=2, fim="11:00"),
    ]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 3
    assert r["mediana_horas"] == pytest.approx(2.0)


def test_falhas_antes_de_qualquer_sucesso_nao_abrem_episodio():
    runs = [
        run("08:00", "failure"),
        run("09:00", "failure"),
        run("10:00", "success"),
    ]
    r = tempo_recuperacao(runs)
    assert r["n_episodios"] == 0
    assert r["falhas_sem_sucesso_anterior"] == 2


def test_episodio_atravessando_dias():
    runs = [
        run("09:00", "success", dia="2026-03-10"),
        run("22:00", "failure", dia="2026-03-10"),
        run("06:00", "success", dia="2026-03-11", fim="06:30"),
    ]
    assert tempo_recuperacao(runs)["mediana_horas"] == pytest.approx(8.5)


def test_usa_created_at_quando_falta_run_started_at():
    r1 = run("09:00", "success")
    r2 = run("10:00", "failure")
    r2["run_started_at"] = None
    r3 = run("11:00", "success", fim="11:00")
    assert tempo_recuperacao([r1, r2, r3])["mediana_horas"] == pytest.approx(1.0)


def test_repo_sem_runs():
    r = tempo_recuperacao([])
    assert r == {
        "mediana_horas": None,
        "n_episodios": 0,
        "n_censurados": 0,
        "prop_censurados": None,
        "falhas_sem_sucesso_anterior": 0,
    }


def test_episodio_aceita_datetime():
    ini = datetime(2026, 3, 10, 10, tzinfo=timezone.utc)
    fim = datetime(2026, 3, 10, 12, tzinfo=timezone.utc)
    ep = Episodio(1, ini, fim)
    assert not ep.censurado
    assert ep.horas == 2
    assert Episodio(1, ini, None).horas is None
