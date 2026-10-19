import math

import pandas as pd
import pytest

from analises import comparar_replicacao as cr


@pytest.fixture
def original():
    return pd.DataFrame({
        "repo": ["a/a", "b/b", "c/c", "d/d"],
        "deployment_frequency": [1.0, 2.0, 0.5, 4.0],
        "lead_time_a_horas": [100.0, 200.0, 50.0, 0.0],
        "estrelas": [1000, 2000, 3000, 4000],
        "dora": ["High", "Elite", "Low", "Medium"],
    })


@pytest.fixture
def replica():
    return pd.DataFrame({
        "repo": ["a/a", "b/b", "c/c"],
        "deployment_frequency": [1.0, 2.1, 0.5],
        "lead_time_a_horas": [100.0, 400.0, None],
        "estrelas": [1010, 2010, 3010],
        "dora": ["High", "High", "Low"],
    })


def test_diferenca_relativa():
    assert cr.diferenca_relativa(100, 110) == pytest.approx(0.10)
    assert cr.diferenca_relativa(0, 0) == 0.0
    assert cr.diferenca_relativa(0, 5) == math.inf
    assert math.isnan(cr.diferenca_relativa(float("nan"), 5))


def test_metricas_comuns_ignora_metadados_e_dora(original, replica):
    assert cr.metricas_comuns(original, replica, "repo", "dora") == ["deployment_frequency", "lead_time_a_horas"]


def test_comparar_so_pareia_repos_em_comum(original, replica):
    longo = cr.comparar(original, replica, "repo", ["deployment_frequency", "lead_time_a_horas"])
    assert len(longo) == 3 * 2
    b = longo[(longo["repo"] == "b/b") & (longo["metrica"] == "lead_time_a_horas")].iloc[0]
    assert b["dif_relativa"] == pytest.approx(1.0)
    c = longo[(longo["repo"] == "c/c") & (longo["metrica"] == "lead_time_a_horas")].iloc[0]
    assert c["so_um_lado_tem_valor"] is True or c["so_um_lado_tem_valor"] == True  # noqa: E712


def test_resumo_por_metrica(original, replica):
    longo = cr.comparar(original, replica, "repo", ["deployment_frequency", "lead_time_a_horas"])
    res = cr.resumo_por_metrica(longo, 0.10).set_index("metrica")
    assert res.loc["deployment_frequency", "pct_dentro_da_tolerancia"] == pytest.approx(100.0)  # 0%, 5%, 0%
    assert res.loc["lead_time_a_horas", "n_comparados"] == 2
    assert res.loc["lead_time_a_horas", "pct_dentro_da_tolerancia"] == pytest.approx(50.0)
    assert res.loc["lead_time_a_horas", "n_so_um_lado_tem_valor"] == 1


def test_concordancia_dora(original, replica):
    d = cr.concordancia_dora(original, replica, "repo", "dora")
    assert d["n"] == 3
    assert d["pct_mesma_classificacao"] == pytest.approx(200 / 3)
    assert list(d["divergentes"].iloc[0]) == ["b/b", "Elite", "High"]


def test_issues_so_para_o_que_passa_da_tolerancia(original, replica):
    longo = cr.comparar(original, replica, "repo", ["deployment_frequency", "lead_time_a_horas"])
    resumo = cr.resumo_por_metrica(longo, 0.10)
    dora = cr.concordancia_dora(original, replica, "repo", "dora")
    txt = cr.redigir_issues(resumo, longo, dora, ["z/z"], 0.10, comando="python -m pipeline")
    assert "divergência em `lead_time_a_horas`" in txt
    assert "divergência em `deployment_frequency`" not in txt  # mediana 0%
    assert "classificação DORA diferente" in txt and "| b/b | Elite | High |" in txt
    assert "`z/z`" in txt and "python -m pipeline" in txt


def test_sem_divergencia_nao_gera_issue():
    df = pd.DataFrame({"repo": ["a/a"], "x": [1.0], "dora": ["High"]})
    longo = cr.comparar(df, df, "repo", ["x"])
    txt = cr.redigir_issues(cr.resumo_por_metrica(longo), longo, cr.concordancia_dora(df, df, "repo", "dora"), [])
    assert "Nenhuma divergência" in txt


def test_main_gera_arquivos(original, replica, tmp_path):
    original.to_csv(tmp_path / "o.csv", index=False)
    replica.to_csv(tmp_path / "r.csv", index=False)
    (tmp_path / "amostra.txt").write_text("a/a\nb/b\nc/c\nd/d\n", encoding="utf-8")
    cr.main(["--original", str(tmp_path / "o.csv"), "--replica", str(tmp_path / "r.csv"),
             "--amostra", str(tmp_path / "amostra.txt"), "--saida", str(tmp_path / "s")])
    texto = (tmp_path / "s" / "issues_divergencia.md").read_text(encoding="utf-8")
    assert "não aparecem no resultado da replicação" in texto and "`d/d`" in texto
    assert (tmp_path / "s" / "replicacao_resumo.csv").exists()
