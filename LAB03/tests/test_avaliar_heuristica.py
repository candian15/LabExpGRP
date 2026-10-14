from datetime import date

import pytest

from validacao.avaliar_heuristica import (
    avaliar,
    carregar_consenso,
    prever,
    registrar,
    tabela_markdown,
)


def test_exemplo_do_enunciado():
    """40 marcadas, 30 confirmadas, 50 corretivas no total: P = 75%, R = 60%, F1 ~ 0,67."""
    consenso, previsto = {}, {}
    for i in range(30):  # verdadeiros positivos
        consenso[("o/r", f"tp{i}")] = True
        previsto[("o/r", f"tp{i}")] = True
    for i in range(10):  # falsos positivos
        consenso[("o/r", f"fp{i}")] = False
        previsto[("o/r", f"fp{i}")] = True
    for i in range(20):  # falsos negativos
        consenso[("o/r", f"fn{i}")] = True
        previsto[("o/r", f"fn{i}")] = False
    for i in range(40):  # verdadeiros negativos
        consenso[("o/r", f"tn{i}")] = False
        previsto[("o/r", f"tn{i}")] = False
    r = avaliar(consenso, previsto)
    assert (r["vp"], r["fp"], r["fn"], r["vn"]) == (30, 10, 20, 40)
    assert r["precisao"] == pytest.approx(0.75)
    assert r["recall"] == pytest.approx(0.60)
    assert r["f1"] == pytest.approx(0.6667, abs=1e-3)
    assert r["atinge_limiar"] is False


def test_concordancia_perfeita_atinge_o_limiar():
    c = {("o/r", "a"): True, ("o/r", "b"): False}
    r = avaliar(c, dict(c))
    assert r["f1"] == 1.0 and r["atinge_limiar"] is True


def test_sem_nenhuma_corretiva_prevista_nao_quebra():
    c = {("o/r", "a"): True, ("o/r", "b"): False}
    r = avaliar(c, {("o/r", "a"): False, ("o/r", "b"): False})
    assert r["precisao"] == 0.0 and r["recall"] == 0.0 and r["f1"] == 0.0


def test_release_sem_predicao_fica_de_fora():
    c = {("o/r", "a"): True, ("o/r", "fora"): True}
    r = avaliar(c, {("o/r", "a"): True})
    assert r["n"] == 1
    assert r["sem_predicao"] == 1


def test_consenso_vazio():
    assert avaliar({}, {})["n"] == 0


def test_carregar_consenso_aceita_sim_nao_e_acentos(tmp_path):
    arq = tmp_path / "consenso.csv"
    arq.write_text("repo,tag,corretiva\no/r,v1.0.1,sim\no/r,v1.1.0,não\no/r,v1.2.0,nao\n", encoding="utf-8")
    c = carregar_consenso(arq)
    assert c == {("o/r", "v1.0.1"): True, ("o/r", "v1.1.0"): False, ("o/r", "v1.2.0"): False}


def test_carregar_consenso_colunas_personalizadas(tmp_path):
    arq = tmp_path / "c.csv"
    arq.write_text("repositorio;release;rotulo\n".replace(";", ",") + "o/r,v1,1\n", encoding="utf-8")
    assert carregar_consenso(arq, "repositorio", "release", "rotulo") == {("o/r", "v1"): True}


def test_rotulo_invalido_levanta_erro(tmp_path):
    arq = tmp_path / "c.csv"
    arq.write_text("repo,tag,corretiva\no/r,v1,incerto\n", encoding="utf-8")
    with pytest.raises(ValueError):
        carregar_consenso(arq)


def test_prever_usa_a_heuristica_escolhida():
    comps = {
        "o/r": [
            {"tag_name": "v1.0.0", "published_at": "2026-03-01T00:00:00Z", "anterior": "v0.9.0",
             "commits": [{"message": "feat"}]},
            {"tag_name": "v1.0.1", "published_at": "2026-03-02T00:00:00Z", "anterior": "v1.0.0",
             "commits": [{"message": "chore"}]},
        ]
    }
    assert prever(comps, "v1") == {("o/r", "v1.0.0"): False, ("o/r", "v1.0.1"): True}
    assert prever(comps, "v3") == {("o/r", "v1.0.0"): False, ("o/r", "v1.0.1"): False}


def test_registrar_acrescenta_ao_historico(tmp_path):
    arq = tmp_path / "validacao" / "historico.md"
    res = {"v1": avaliar({("o/r", "a"): True}, {("o/r", "a"): True})}
    registrar(res, arq, "primeira rodada", hoje=date(2026, 10, 20))
    registrar(res, arq, hoje=date(2026, 10, 21))
    texto = arq.read_text(encoding="utf-8")
    assert "Rodada de 2026-10-20" in texto and "primeira rodada" in texto and "Rodada de 2026-10-21" in texto
    assert "| v1 | 1 |" in texto


def test_tabela_markdown_formata_percentuais():
    res = {"v1": avaliar({("o/r", "a"): True}, {("o/r", "a"): True})}
    assert "1.00" in tabela_markdown(res)
