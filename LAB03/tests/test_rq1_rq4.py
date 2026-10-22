import numpy as np
import pandas as pd
import pytest

from analises import rq1_rq4_descritiva as rq14


@pytest.fixture
def df():
    """20 repositórios: 4 sem episódio de recuperação e 16 com."""
    n = 20
    sem_episodio = [0] * 4 + [3] * 16
    return pd.DataFrame({
        "repo": [f"o/r{i}" for i in range(n)],
        "deployment_frequency": np.arange(1.0, n + 1.0),
        "lead_time_a_horas": np.arange(10.0, 10.0 * (n + 1), 10.0),
        "lead_time_b_horas": np.arange(20.0, 20.0 * (n + 1), 20.0),
        "cfr_ci": np.linspace(0.0, 0.38, n),
        "cfr_entrega": np.linspace(0.0, 0.76, n),
        # quem não tem episódio não tem tempo de recuperação nem censura
        "recuperacao_horas": [np.nan] * 4 + list(np.arange(1.0, 17.0)),
        "n_episodios": sem_episodio,
        "prop_censurados": [np.nan] * 4 + [0.5] * 16,
        "n_runs_validos": np.arange(50, 50 + n),
        "nota_frequencia": [4] * 5 + [3] * 5 + [2] * 5 + [1] * 5,
        "nota_lead_time": [4] * 2 + [3] * 8 + [2] * 8 + [1] * 2,
        "nota_cfr": [4] * 20,
        "nota_recuperacao": [3] * 20,
        "dora_nota": [4] * 5 + [3] * 5 + [2] * 5 + [1] * 5,
        "dora": ["Elite"] * 5 + ["High"] * 5 + ["Medium"] * 5 + ["Low"] * 5,
        "motivo_descarte": pd.Series([None] * n, dtype=object),
    })


# ------------------------------------------------------------------ resumo
def test_resumo_bate_com_o_pandas(df):
    r = rq14.resumo(df["deployment_frequency"])
    s = df["deployment_frequency"]
    assert r["n"] == 20
    assert r["mediana"] == pytest.approx(float(s.median()))
    assert r["q1"] == pytest.approx(float(s.quantile(0.25)))
    assert r["q3"] == pytest.approx(float(s.quantile(0.75)))
    assert r["iqr"] == pytest.approx(r["q3"] - r["q1"])
    assert (r["minimo"], r["maximo"]) == (1.0, 20.0)


def test_resumo_ignora_ausentes(df):
    assert rq14.resumo(df["recuperacao_horas"])["n"] == 16


def test_resumo_de_serie_vazia_nao_quebra():
    r = rq14.resumo(pd.Series([], dtype=float))
    assert r["n"] == 0 and np.isnan(r["mediana"])


# ------------------------------------------------------- tabela descritiva
def test_tabela_tem_uma_linha_por_metrica_mais_a_censura(df):
    t = rq14.tabela_descritiva(df, rq14.metricas("cfr_entrega"))
    assert list(t["metrica"]) == ["deployment_frequency", "lead_time_a", "lead_time_b",
                                  "cfr_a_ci", "cfr_b_entrega", "recuperacao", "prop_censurados"]
    assert list(t["rq"]) == ["RQ01", "RQ02", "RQ02", "RQ03", "RQ03", "RQ04", "RQ04"]


def test_recuperacao_exclui_quem_nao_tem_episodio(df):
    t = rq14.tabela_descritiva(df, rq14.metricas("cfr_entrega"))
    linha = t[t["metrica"] == "recuperacao"].iloc[0]
    assert linha["n"] == 16                      # 20 - 4 sem episódio
    assert linha["mediana"] == pytest.approx(8.5)  # mediana de 1..16


def test_censura_so_conta_quem_tem_episodio(df):
    t = rq14.tabela_descritiva(df, rq14.metricas("cfr_entrega"))
    linha = t[t["metrica"] == "prop_censurados"].iloc[0]
    assert linha["n"] == 16 and linha["mediana"] == pytest.approx(0.5)


def test_tabela_usa_a_coluna_de_cfr_b_informada(df):
    df = df.rename(columns={"cfr_entrega": "cfr_b"})
    t = rq14.tabela_descritiva(df, rq14.metricas("cfr_b"))
    assert t[t["metrica"] == "cfr_b_entrega"].iloc[0]["n"] == 20


# ------------------------------------------------------------ distribuições
def test_distribuicao_dora_na_ordem_elite_low(df):
    d = rq14.distribuicao_dora(df)
    assert list(d["categoria"]) == ["Elite", "High", "Medium", "Low"]
    assert list(d["n"]) == [5, 5, 5, 5]
    assert d["pct"].sum() == pytest.approx(100.0)


def test_categoria_fora_da_escala_ainda_aparece(df):
    df.loc[0, "dora"] = "Desconhecida"
    d = rq14.distribuicao_dora(df)
    assert d[d["categoria"] == "Elite"].iloc[0]["n"] == 4
    assert "Desconhecida" in set(d["categoria"])
    assert d["n"].sum() == 20


def test_distribuicao_de_notas_mapeia_nota_para_categoria(df):
    d = rq14.distribuicao_notas(df)
    assert set(d["nota_de"]) == {"nota_frequencia", "nota_lead_time", "nota_cfr", "nota_recuperacao"}
    assert list(d[d["nota_de"] == "nota_cfr"]["n"]) == [20, 0, 0, 0]  # todos Elite
    elite = d[(d["nota_de"] == "nota_frequencia") & (d["nota"] == 4)].iloc[0]
    assert elite["categoria"] == "Elite" and elite["pct"] == pytest.approx(25.0)


def test_notas_ausentes_no_csv_nao_quebram(df):
    d = rq14.distribuicao_notas(df.drop(columns=["nota_cfr"]))
    assert "nota_cfr" not in set(d["nota_de"]) and len(d) == 12


# ------------------------------------------------------ sem recuperação
def test_lista_os_repositorios_sem_episodio(df):
    fora = rq14.sem_recuperacao(df)
    assert len(fora) == 4
    assert set(fora["repo"]) == {"o/r0", "o/r1", "o/r2", "o/r3"}
    assert (fora["n_episodios"] == 0).all()


def test_sem_a_coluna_de_episodios_devolve_vazio(df):
    assert rq14.sem_recuperacao(df.drop(columns=["n_episodios"])).empty


# ------------------------------------------------------------------- main
def test_main_escreve_os_quatro_csvs_e_os_tres_graficos(df, tmp_path):
    csv = tmp_path / "repositorios.csv"
    df.to_csv(csv, index=False)
    saida = tmp_path / "resultados"
    rq14.main(["--csv", str(csv), "--saida", str(saida)])

    for nome in ("rq1_rq4_descritiva", "rq1_rq4_dora", "rq1_rq4_notas", "rq1_rq4_sem_recuperacao"):
        assert (saida / f"{nome}.csv").exists(), nome
    for nome in ("rq1_rq4_distribuicoes", "rq1_rq4_pares", "rq1_rq4_dora"):
        assert (saida / f"{nome}.png").stat().st_size > 1000, nome

    t = pd.read_csv(saida / "rq1_rq4_descritiva.csv")
    assert len(t) == 7
    assert pd.read_csv(saida / "rq1_rq4_sem_recuperacao.csv").shape[0] == 4


def test_main_ignora_os_repositorios_descartados(df, tmp_path):
    df.loc[:9, "motivo_descarte"] = "poucas_releases"
    csv = tmp_path / "repositorios.csv"
    df.to_csv(csv, index=False)
    saida = tmp_path / "resultados"
    rq14.main(["--csv", str(csv), "--saida", str(saida)])
    assert pd.read_csv(saida / "rq1_rq4_dora.csv")["n"].sum() == 10
