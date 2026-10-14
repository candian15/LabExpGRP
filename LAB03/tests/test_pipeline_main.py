"""Testes do comando único: leitura do config e consolidação das métricas."""

from datetime import date

import pytest

from metricas.cfr_entrega import VERSAO_PADRAO
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
    assert cfg["heuristica_cfrb"] == VERSAO_PADRAO


def test_config_escolhe_a_versao_da_heuristica_do_cfr_b(tmp_path):
    texto = "janela:\n  inicio: 2025-10-01\n  fim: 2026-09-30\nselecao:\n  heuristica_cfrb: v3\n"
    assert carregar_config(escrever(tmp_path, texto))["heuristica_cfrb"] == "v3"


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


def comparacao(tag, dia, anterior, mensagens=("feat: nova tela",)):
    """Uma release da janela, no formato que pipeline.coleta_releases devolve."""
    return {
        "tag_name": tag,
        "published_at": f"2026-0{dia[0]}-{dia[1:]}T00:00:00Z",
        "anterior": anterior,
        "status": "ok",
        "commits": [{"sha": f"{tag}-{i}", "data": f"2026-0{dia[0]}-{dia[1:]}T00:00:00Z",
                     "message": m} for i, m in enumerate(mensagens)],
    }


def test_metricas_trazem_as_duas_variantes_do_cfr():
    # Exemplo do enunciado: v2.3.0 é seguida em 2 dias por v2.3.1, que só muda o
    # patch e traz um commit de fix -> v2.3.0 falhou. v2.4.0 é seguida por
    # v2.5.0 (minor, sem fix) -> não falhou.
    comparacoes = [
        comparacao("v2.3.0", "510", "v2.2.0"),
        comparacao("v2.3.1", "512", "v2.3.0", ("fix: crash ao abrir arquivo",)),
        comparacao("v2.4.0", "601", "v2.3.1"),
        comparacao("v2.5.0", "620", "v2.4.0"),
    ]
    runs = [run("09:00", "success"), run("10:00", "failure"), run("11:00", "success")]
    m = metricas_do_repo({"n_releases": 4}, comparacoes, runs, INICIO, FIM)

    # CFR (a) é proxy de CI; CFR (b) é proxy de entrega. São métricas diferentes.
    assert m["cfr_ci"] == pytest.approx(1 / 3, abs=1e-4)
    assert m["cfr_entrega"] == pytest.approx(0.25)   # 1 falha em 4 releases avaliadas
    assert m["cfrb_releases_avaliadas"] == 4
    assert m["cfrb_releases_falha"] == 1
    assert m["cfrb_releases_censuradas"] == 0
    assert m["cfrb_releases_corretivas"] == 1
    assert m["cfrb_heuristica"] == VERSAO_PADRAO


def test_release_nos_ultimos_7_dias_da_janela_e_censurada():
    # A janela termina em 30/09: uma release de 28/09 ainda não pode ser avaliada.
    comparacoes = [
        comparacao("v1.0", "510", "v0.9"),
        {"tag_name": "v1.1", "published_at": "2026-09-28T00:00:00Z", "anterior": "v1.0",
         "status": "ok", "commits": [{"sha": "x", "data": "2026-09-27T00:00:00Z", "message": "feat"}]},
    ]
    m = metricas_do_repo({"n_releases": 2}, comparacoes, [], INICIO, FIM)
    assert m["cfrb_releases_avaliadas"] == 1
    assert m["cfrb_releases_censuradas"] == 1


def test_a_classificacao_dora_continua_usando_o_cfr_a():
    # Combinação de referência C1 da RQ 07: CFR (a). Aqui o CFR (b) é 0 (Elite) e
    # o CFR (a) é 1,0 (Low); a nota tem que seguir o (a).
    runs = [run("10:00", "failure"), run("11:00", "timed_out")]
    m = metricas_do_repo({"n_releases": 1}, [comparacao("v1.0", "510", "v0.9")], runs, INICIO, FIM)
    assert (m["cfr_ci"], m["cfr_entrega"]) == (1.0, 0.0)
    assert m["nota_cfr"] == 1


def test_heuristica_escolhida_muda_o_resultado():
    # v1 marca como corretiva se houver QUALQUER commit de fix; v2 exige metade.
    comparacoes = [
        comparacao("v1.0", "510", "v0.9"),
        comparacao("v1.1", "512", "v1.0", ("fix: typo", "feat: a", "feat: b", "feat: c")),
    ]
    v1 = metricas_do_repo({"n_releases": 2}, comparacoes, [], INICIO, FIM, heuristica="v1")
    v2 = metricas_do_repo({"n_releases": 2}, comparacoes, [], INICIO, FIM, heuristica="v2")
    assert v1["cfrb_releases_falha"] == 1
    assert v2["cfrb_releases_falha"] == 0
