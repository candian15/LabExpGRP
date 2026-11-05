import numpy as np
import pandas as pd
import pytest
import yaml

from src import coletar_dados_reais as col
from src import graficos_g1 as g1
from src import parametros_reais as par


# ---------------------------------------------------------------- coleta (sem rede)
def item(numero, criado, mesclado, tipo="User"):
    return {"number": numero, "created_at": criado, "html_url": f"https://github.com/o/r/pull/{numero}",
            "user": {"login": "x", "type": tipo}, "pull_request": {"merged_at": mesclado}}


def test_horas_ate_merge():
    assert col.horas_ate_merge(item(1, "2026-08-01T00:00:00Z", "2026-08-01T03:30:00Z")) == pytest.approx(3.5)
    assert col.horas_ate_merge({"created_at": "2026-08-01T00:00:00Z", "pull_request": {"merged_at": None}}) is None


def test_elegiveis_descarta_bots_e_nao_mesclados():
    itens = [item(1, "2026-08-01T00:00:00Z", "2026-08-02T00:00:00Z"),
             item(2, "2026-08-01T00:00:00Z", "2026-08-02T00:00:00Z", tipo="Bot"),
             {"number": 3, "created_at": "2026-08-01T00:00:00Z", "user": {"login": "x", "type": "User"},
              "pull_request": {"merged_at": None}, "html_url": ""},
             item(4, "2026-08-02T00:00:00Z", "2026-08-01T00:00:00Z")]  # merge antes da criação: dado inválido
    out = col.elegiveis(itens, "com_bot")
    assert [r["pr"] for r in out] == [1] and out[0]["horas_ate_merge"] == 24.0 and out[0]["grupo"] == "com_bot"


def test_amostrar_e_reproduzivel_e_respeita_o_tamanho():
    pool = [{"pr": i} for i in range(100)]
    a = col.amostrar(pool, 30, np.random.default_rng(42))
    b = col.amostrar(pool, 30, np.random.default_rng(42))
    assert a == b and len(a) == 30 and len({r["pr"] for r in a}) == 30
    assert col.amostrar(pool[:10], 30, np.random.default_rng(1)) == pool[:10]


# -------------------------------------------------------------------- parâmetros
@pytest.fixture
def reais():
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "grupo": ["sem_bot"] * 300 + ["com_bot"] * 300,
        "horas_ate_merge": np.concatenate([rng.lognormal(2.0, 1.5, 300), rng.lognormal(0.5, 1.0, 300)]),
    })


def test_descrever_recupera_os_parametros_da_lognormal(reais):
    d = par.descrever(reais.loc[reais["grupo"] == "sem_bot", "horas_ate_merge"])
    assert d["mu_log"] == pytest.approx(2.0, abs=0.2)
    assert d["sigma_log"] == pytest.approx(1.5, abs=0.15)
    assert d["assimetria"] > 1 and d["n"] == 300


def test_descrever_ignora_zeros_e_nulos():
    d = par.descrever(pd.Series([0.0, np.nan, 1.0, 2.0, 4.0, 8.0]))
    assert d["n"] == 4


def test_montar_cenario_convencao_do_efeito(reais):
    cen = par.montar_cenario(par.tabela_descritiva(reais), {"repositorio": "o/r"})
    assert cen["controle"] == "sem_bot" and cen["tratamento"] == "com_bot"
    assert cen["grupos"]["sem_bot"]["mediana"] == pytest.approx(np.exp(cen["grupos"]["sem_bot"]["mu"]), rel=1e-3)
    assert cen["efeitos_razao_medianas"][0] == 1.0 and len(cen["efeitos_razao_medianas"]) >= 5
    assert cen["razao_medianas_observada"] < 1


def test_main_grava_yaml_e_csv(reais, tmp_path):
    reais.to_csv(tmp_path / "d.csv", index=False)
    par.main(str(tmp_path / "d.csv"), str(tmp_path / "c" / "cenario.yaml"), str(tmp_path / "e.csv"))
    cfg = yaml.safe_load((tmp_path / "c" / "cenario.yaml").read_text(encoding="utf-8"))
    assert cfg["semente"] == 42 and cfg["n_por_grupo"] == 300
    assert set(pd.read_csv(tmp_path / "e.csv")["grupo"]) == {"sem_bot", "com_bot"}


# --------------------------------------------------------------------------- G1
def test_simulacao_g1_usa_os_parametros_do_cenario():
    cfg = {"grupos": {"sem_bot": {"mu": 2.0, "sigma": 1.0}, "com_bot": {"mu": 0.0, "sigma": 0.5}}}
    sim = g1.simular_para_g1(cfg, np.random.default_rng(42), n=5000)
    med = sim.groupby("grupo")["horas_ate_merge"].median()
    assert med["sem_bot"] == pytest.approx(np.exp(2.0), rel=0.1)
    assert med["com_bot"] == pytest.approx(1.0, rel=0.1)


def test_fig_g1_tem_quatro_paineis_com_rotulos(reais):
    cfg = {"grupos": {"sem_bot": {"mu": 2.0, "sigma": 1.5}, "com_bot": {"mu": 0.5, "sigma": 1.0}}}
    fig = g1.fig_g1(reais, g1.simular_para_g1(cfg, np.random.default_rng(1), n=200))
    eixos = fig.get_axes()
    assert len(eixos) == 4
    assert all("horas" in e.get_xlabel() for e in eixos[2:])
    assert "G1" in fig._suptitle.get_text()
    g1.plt.close(fig)
