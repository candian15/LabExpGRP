import numpy as np
import pandas as pd
import pytest
from scipy.stats import kruskal, mannwhitneyu, spearmanr
from statsmodels.stats.multitest import multipletests

from analises import rq5_correlacao as rq5
from analises import rq6_fatores as rq6


@pytest.fixture
def df():
    rng = np.random.default_rng(1)
    n = 120
    freq = rng.lognormal(0, 1, n)
    return pd.DataFrame({
        "repo": [f"o/r{i}" for i in range(n)],
        "deployment_frequency": freq,
        "cfr_ci": np.clip(0.4 - 0.1 * np.log(freq) + rng.normal(0, 0.05, n), 0, 1),
        "cfr_entrega": rng.uniform(0, 0.5, n),
        "lead_time_a_horas": rng.lognormal(3, 1, n),
        "lead_time_b_horas": rng.lognormal(2, 1, n),
        "recuperacao_horas": rng.lognormal(1, 1, n),
        "linguagem": rng.choice(["Python", "Go", "Java", "Rust", "C", "Ruby", "Lua"], n),
        "estrelas": rng.integers(1000, 50000, n),
        "contribuidores": rng.integers(1, 400, n),
        "idade_anos": rng.uniform(1, 15, n),
        "motivo_descarte": pd.Series([None] * n, dtype=object),
    })


# ------------------------------------------------------------------------------ RQ 05
def test_spearman_bate_com_o_scipy(df):
    r = rq5.correlacao(df, "deployment_frequency", "cfr_ci")
    ref = spearmanr(df["deployment_frequency"], df["cfr_ci"])
    assert r["rho"] == pytest.approx(ref.statistic)
    assert r["p"] == pytest.approx(ref.pvalue)
    assert r["n"] == 120
    assert r["rho"] < -0.5  # construído com relação inversa forte


def test_spearman_ignora_linhas_sem_valor(df):
    df.loc[:9, "cfr_entrega"] = np.nan
    assert rq5.correlacao(df, "deployment_frequency", "cfr_entrega")["n"] == 110


def test_spearman_com_valores_constantes_nao_quebra():
    d = pd.DataFrame({"x": [1, 2, 3, 4], "y": [0.0, 0.0, 0.0, 0.0]})
    assert np.isnan(rq5.correlacao(d, "x", "y")["rho"])


@pytest.mark.parametrize("rho,txt", [(0.05, "desprezível positiva"), (-0.2, "fraca negativa"),
                                     (0.4, "moderada positiva"), (-0.8, "forte negativa")])
def test_interpretar_rho(rho, txt):
    assert rq5.interpretar(rho) == txt


def test_rq5_main_gera_csv_e_grafico(df, tmp_path):
    csv = tmp_path / "repositorios.csv"
    df.to_csv(csv, index=False)
    rq5.main(["--csv", str(csv), "--saida", str(tmp_path / "saida")])
    tab = pd.read_csv(tmp_path / "saida" / "rq5_spearman.csv")
    assert list(tab["variante_cfr"]) == ["a (CI)", "b (entrega)"]
    assert (tmp_path / "saida" / "rq5_dispersao.png").stat().st_size > 1000


# ------------------------------------------------------------------------------ RQ 06
def test_cliffs_delta_extremos_e_formula():
    assert rq6.cliffs_delta(25, 5, 5) == 1.0  # x sempre maior que y
    assert rq6.cliffs_delta(0, 5, 5) == -1.0
    assert rq6.cliffs_delta(12.5, 5, 5) == 0.0
    x, y = [5, 6, 7, 8], [1, 2, 3, 9]
    u = mannwhitneyu(x, y).statistic
    assert rq6.cliffs_delta(u, 4, 4) == pytest.approx(0.5)  # 12 de 16 pares x>y, 4 de 16 y>x: (12-4)/16


@pytest.mark.parametrize("d,txt", [(0.1, "desprezível"), (0.2, "pequeno"), (-0.4, "médio"), (0.9, "grande")])
def test_interpretar_delta(d, txt):
    assert rq6.interpretar_delta(d) == txt


def test_epsilon_quadrado():
    assert rq6.epsilon_quadrado(10.0, 101) == pytest.approx(0.1)


def test_quartis_e_linguagem_agrupada(df):
    q = rq6.quartis(df["estrelas"])
    assert set(q.dropna().unique()) == {"Q1", "Q2", "Q3", "Q4"}
    ling = rq6.linguagem_agrupada(df["linguagem"])
    assert ling.nunique() == 6 and "Outras" in set(ling)


def test_kruskal_com_tres_ou_mais_grupos():
    v = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] * 1, dtype=float)
    g = pd.Series(["A"] * 5 + ["B"] * 5 + ["C"] * 5)
    r = rq6.testar(v, g)
    ref = kruskal(v[:5], v[5:10], v[10:])
    assert r["teste"] == "Kruskal-Wallis"
    assert r["estatistica"] == pytest.approx(ref.statistic)
    assert r["efeito"] == pytest.approx(ref.statistic / 14)


def test_dois_grupos_usam_mann_whitney():
    v = pd.Series(list(range(10)) + list(range(100, 110)), dtype=float)
    g = pd.Series(["A"] * 10 + ["B"] * 10)
    r = rq6.testar(v, g)
    assert r["teste"] == "Mann-Whitney"
    assert r["efeito"] == pytest.approx(-1.0)
    assert r["interpretacao_efeito"] == "grande"


def test_grupo_pequeno_e_descartado():
    v = pd.Series([1.0] * 10 + [5.0] * 10 + [9.0] * 2)
    g = pd.Series(["A"] * 10 + ["B"] * 10 + ["C"] * 2)
    assert rq6.testar(v, g)["k_grupos"] == 2


def test_um_grupo_so_devolve_none():
    assert rq6.testar(pd.Series([1.0, 2, 3, 4, 5, 6]), pd.Series(["A"] * 6)) is None


def test_holm_e_aplicado_em_conjunto(df):
    res = rq6.rodar(df, rq6.metricas_padrao(df, "cfr_entrega"))
    assert len(res) == 4 * 6  # 4 fatores x 6 métricas
    esperado = multipletests(res["p"], method="holm")[1]
    assert res["p_holm"].to_numpy() == pytest.approx(esperado)
    assert (res["p_holm"] >= res["p"] - 1e-12).all()


def test_efeito_detectado_quando_ha_diferenca_real(df):
    df.loc[df["linguagem"] == "Python", "lead_time_a_horas"] *= 50
    res = rq6.rodar(df, rq6.metricas_padrao(df, "cfr_entrega"))
    linha = res[(res["fator"] == "linguagem") & (res["metrica"] == "lead_time_a")].iloc[0]
    assert linha["significativo_holm"] and linha["efeito"] > 0.1


def test_tipo_do_projeto_entra_como_fator(df):
    tipos = pd.DataFrame({"repo": df["repo"], "tipo": np.where(np.arange(len(df)) % 2, "biblioteca", "aplicação")})
    res = rq6.rodar(df, rq6.metricas_padrao(df, "cfr_entrega"), tipos)
    assert "tipo_projeto" in set(res["fator"])
    assert set(res.loc[res["fator"] == "tipo_projeto", "teste"]) == {"Mann-Whitney"}


def test_rq6_main_escreve_csv(df, tmp_path):
    csv = tmp_path / "r.csv"
    df.to_csv(csv, index=False)
    rq6.main(["--csv", str(csv), "--saida", str(tmp_path / "s")])
    assert len(pd.read_csv(tmp_path / "s" / "rq6_testes.csv")) == 24


def test_repositorios_descartados_ficam_de_fora(df, tmp_path):
    df.loc[:19, "motivo_descarte"] = "menos de 5 releases"
    csv = tmp_path / "r.csv"
    df.to_csv(csv, index=False)
    from analises.utils import achar_coluna, carregar_repositorios

    assert len(carregar_repositorios(csv)) == 100
    assert achar_coluna(df, ["cfr_b", "cfr_entrega"]) == "cfr_entrega"
    with pytest.raises(SystemExit):
        achar_coluna(df, ["nao_existe"])


def test_tipos_aceita_coluna_tipo_projeto_e_ignora_vazios(df):
    tipos = pd.DataFrame({"repo": df["repo"], "tipo_projeto": np.where(np.arange(len(df)) % 2, "cli", "biblioteca")})
    tipos.loc[:4, "tipo_projeto"] = ""
    fatores = rq6.montar_fatores(df, tipos)
    assert fatores["tipo_projeto"].notna().sum() == len(df) - 5
