"""Testes do comando único: leitura do config e consolidação das métricas."""

from datetime import date

import pytest

from pipeline.__main__ import CAMPOS_SAIDA, carregar_config, metricas_do_repo
from tests.conftest import run

INICIO, FIM = date(2025, 10, 1), date(2026, 9, 30)
DIA = 24


def escrever(tmp_path, texto):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def test_config_minimo_usa_os_padroes_do_enunciado(tmp_path):
    cfg = carregar_config(escrever(tmp_path, "janela:\n  inicio: 2025-10-01\n  fim: 2026-09-30\n"))
    assert (cfg["inicio"], cfg["fim"]) == (INICIO, FIM)
    assert (cfg["min_releases"], cfg["min_runs"]) == (5, 50)
    assert cfg["faixas_estrelas"] == [">1000"]


def test_config_sem_janela_falha_com_mensagem(tmp_path):
    with pytest.raises(SystemExit, match="janela.inicio"):
        carregar_config(escrever(tmp_path, "selecao:\n  min_runs: 10\n"))


def test_config_aceita_data_entre_aspas(tmp_path):
    cfg = carregar_config(escrever(tmp_path, 'janela:\n  inicio: "2025-10-01"\n  fim: "2026-09-30"\n'))
    assert cfg["inicio"] == INICIO


def test_metricas_do_repo_junta_as_quatro_metricas_e_classifica():
    # 53 releases em ≈ 52,1 semanas -> pouco mais de 1/semana (High).
    # Lead time (a): release de 15/03 com commit mais antigo em 14/03 -> 24 h (High).
    comparacoes = [{
        "tag_name": "v1.1",
        "published_at": "2026-03-15T00:00:00Z",
        "status": "ok",
        "commits": [{"sha": "x", "data": "2026-03-14T00:00:00Z"}],
    }]
    # 1 falha em 4 runs válidos -> CFR 0,25 (High); recuperação 1h20 (High).
    runs = [
        run("09:00", "success", fim="09:05"),
        run("10:00", "failure", fim="10:05"),
        run("11:15", "success", fim="11:20"),
        run("12:00", "success", fim="12:05"),
    ]
    m = metricas_do_repo({"n_releases": 53}, comparacoes, runs, INICIO, FIM)

    assert m["deployment_frequency"] == pytest.approx(1.02, abs=0.01)
    assert m["lead_time_a_horas"] == DIA
    assert m["cfr_ci"] == pytest.approx(0.25)
    assert m["recuperacao_horas"] == pytest.approx(80 / 60, abs=1e-4)
    assert [m["nota_frequencia"], m["nota_lead_time"], m["nota_cfr"], m["nota_recuperacao"]] == [3, 3, 3, 3]
    assert m["dora"] == "High"


def test_metricas_sem_dados_de_lead_time_nao_quebram():
    m = metricas_do_repo({"n_releases": 5}, [], [], INICIO, FIM)
    assert m["lead_time_a_horas"] is None
    assert m["cfr_ci"] is None
    assert m["recuperacao_horas"] is None
    # Só a frequência tem nota (5 releases no ano = menos de 1 por mês = Low),
    # e ela decide a categoria sozinha.
    assert m["dora"] == "Low"


def test_todas_as_chaves_das_metricas_estao_no_csv_final():
    m = metricas_do_repo({"n_releases": 5}, [], [], INICIO, FIM)
    assert set(m) <= set(CAMPOS_SAIDA)
