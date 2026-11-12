"""Testes da S02: leitura dos resultados, G3, G4 e o comando único.

As figuras são testadas pelo que o enunciado cobra delas (um painel por situação, a
linha dos 5%, a legenda com os dois testes), não pelo desenho em si. A leitura é testada
com CSVs montados na hora, para não depender de quais simulações já foram rodadas.
"""

from pathlib import Path

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from src import resultados  # noqa: E402
from src.graficos import CORES, fig_g3, fig_g4  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def tabela(situacao, razoes=(1.0,), n=30, sigma=2.4, taxa=0.05):
    linhas = [{"situacao": situacao, "n": n, "sigma": sigma, "razao": r,
               "teste": teste, "taxa_rejeicao": taxa}
              for r in razoes for teste in CORES]
    return pd.DataFrame(linhas)


@pytest.fixture
def pasta(tmp_path):
    """Uma pasta resultados/ com q1, q2 e q3, como depois que todo mundo rodar."""
    tabela("real").to_csv(tmp_path / "q1.csv", index=False)
    tabela("real", razoes=(1.0, 0.8, 0.6, 0.4, 0.2)).to_csv(tmp_path / "q2.csv", index=False)
    pd.concat([tabela("outliers", razoes=(1.0, 0.5)),
               tabela("bem_comportada", razoes=(1.0, 0.5), sigma=0.3)]
              ).to_csv(tmp_path / "q3.csv", index=False)
    return tmp_path


# ------------------------------------------------------------ leitura dos CSVs
def test_ler_taxas_junta_os_tres_arquivos(pasta):
    taxas = resultados.ler_taxas(pasta)
    assert set(taxas["situacao"]) == {"real", "outliers", "bem_comportada"}
    assert list(taxas.columns) == list(resultados.COLUNAS)


def test_ler_taxas_funciona_sem_o_q3(tmp_path):
    """O G3 e o G4 precisam sair mesmo com a Q3 ainda pendente."""
    tabela("real").to_csv(tmp_path / "q1.csv", index=False)
    assert resultados.situacoes(resultados.ler_taxas(tmp_path)) == ["real"]


def test_ler_taxas_sem_nenhum_arquivo(tmp_path):
    with pytest.raises(FileNotFoundError):
        resultados.ler_taxas(tmp_path)


def test_ler_taxas_cobra_as_colunas(tmp_path):
    pd.DataFrame([{"situacao": "real", "teste": "Welch"}]).to_csv(tmp_path / "q1.csv",
                                                                 index=False)
    with pytest.raises(ValueError):
        resultados.ler_taxas(tmp_path)


def test_razao_1_do_cenario_real_vem_da_q1(tmp_path):
    """Q1 e Q2 estimam a mesma linha; vale a da Q1, que gastou as repetições só nela."""
    tabela("real", taxa=0.0149).to_csv(tmp_path / "q1.csv", index=False)
    tabela("real", razoes=(1.0, 0.2), taxa=0.0141).to_csv(tmp_path / "q2.csv", index=False)

    taxas = resultados.ler_taxas(tmp_path)
    sem_efeito = taxas[taxas["razao"] == 1.0]
    assert len(sem_efeito) == len(CORES), "a linha de razão = 1 ficou duplicada"
    assert set(sem_efeito["taxa_rejeicao"]) == {0.0149}


def test_ordem_das_situacoes_e_a_do_cenario(pasta):
    """Cenário real primeiro; situação desconhecida não some, vai para o fim."""
    tabela("inventada").to_csv(pasta / "q3.csv", mode="a", header=False, index=False)
    assert resultados.situacoes(resultados.ler_taxas(pasta)) == [
        "real", "bem_comportada", "outliers", "inventada"]


def test_erro_tipo_i_pega_so_a_razao_1(pasta):
    taxas = resultados.ler_taxas(pasta)
    assert set(resultados.erro_tipo_i(taxas)["razao"]) == {1.0}


def test_rotulo_mostra_n_e_sigma(pasta):
    rotulos = resultados.rotulos(resultados.ler_taxas(pasta))
    assert "cenário real" in rotulos[0] and "n = 30" in rotulos[0]
    assert "σ = 0,30" in " ".join(rotulos), "o rótulo precisa mostrar o σ da situação"


# ------------------------------------------------------------------ G3 e G4
def test_g3_tem_uma_barra_por_teste_e_situacao(pasta):
    taxas = resultados.ler_taxas(pasta)
    ax = fig_g3(taxas).get_axes()[0]
    grupos = [c for c in ax.containers if hasattr(c, "patches")]
    assert len(grupos) == len(CORES), "o G3 tem um grupo de barras por teste"
    assert all(len(c) == 3 for c in grupos), "uma barra por situação em cada grupo"


def test_g3_tem_a_linha_de_5_por_cento(pasta):
    ax = fig_g3(resultados.ler_taxas(pasta)).get_axes()[0]
    alturas = [linha.get_ydata()[0] for linha in ax.get_lines()]
    assert 0.05 in alturas, "o enunciado pede a linha em 5% no G3"


def test_g3_nomeia_os_dois_testes_na_legenda(pasta):
    ax = fig_g3(resultados.ler_taxas(pasta)).get_axes()[0]
    nomes = [t.get_text() for t in ax.get_legend().get_texts()]
    assert set(CORES) <= set(nomes)


def test_g3_precisa_de_h0_verdadeira(pasta):
    taxas = resultados.ler_taxas(pasta)
    with pytest.raises(ValueError):
        fig_g3(taxas[taxas["razao"] != 1.0])


def test_g4_tem_um_painel_por_situacao(pasta):
    assert len(fig_g4(resultados.ler_taxas(pasta)).get_axes()) == 3


def test_g4_tem_uma_curva_por_teste_com_a_cor_do_teste(pasta):
    ax = fig_g4(resultados.ler_taxas(pasta)).get_axes()[0]
    curvas = {linha.get_label(): linha.get_color() for linha in ax.get_lines()}
    for teste, cor in CORES.items():
        assert curvas.get(teste) == cor, f"a cor do {teste} mudou de um gráfico para o outro"


def test_g4_mostra_o_efeito_crescendo_para_a_direita(pasta):
    ax = fig_g4(resultados.ler_taxas(pasta)).get_axes()[0]
    esquerda, direita = ax.get_xlim()
    assert esquerda > direita, "a razão de medianas diminui quando o efeito aumenta"


def test_eixos_tem_nome_nos_dois_graficos(pasta):
    """O enunciado cobra título, eixos com nome e legenda em todos os gráficos."""
    taxas = resultados.ler_taxas(pasta)
    for fig in (fig_g3(taxas), fig_g4(taxas)):
        ax = fig.get_axes()[0]
        assert ax.get_xlabel(), "eixo x sem nome"
        assert ax.get_ylabel(), "eixo y sem nome"
        assert ax.get_title() or fig.get_suptitle(), "figura sem título"
        assert ax.get_legend() is not None, "figura sem legenda"


# --------------------------------------------------------------- comando único
def test_etapas_cobrem_os_arquivos_de_resultados():
    from src.rodar_tudo import ETAPAS

    saidas = [s for etapa in ETAPAS for s in etapa.saidas]
    assert len(saidas) == len(set(saidas)), "duas etapas gravando o mesmo arquivo"
    for arquivo in ("resultados/q1.csv", "resultados/q2.csv", "resultados/q3.csv",
                    "resultados/dados_reais.csv"):
        assert arquivo in saidas, f"{arquivo} não é gerado pelo comando único"


def test_etapa_sem_modulo_fica_pendente_em_vez_de_quebrar():
    from src.rodar_tudo import PENDENTE, Etapa, rodar

    etapa = Etapa(nome="etapa que ainda não existe", de_quem="ninguém",
                  saidas=("resultados/nao_existe.csv",), modulo="src.modulo_inexistente")
    assert rodar(etapa) == PENDENTE


def test_etapa_que_quebra_e_reportada_como_erro():
    from src.rodar_tudo import ERRO, Etapa, rodar

    def explode():
        raise RuntimeError("falhou de propósito")

    etapa = Etapa(nome="etapa com defeito", de_quem="ninguém", saidas=(), acao=explode)
    assert rodar(etapa) == ERRO


def test_as_quatro_figuras_sao_geradas_pelo_comando_unico():
    from src.rodar_tudo import ETAPAS

    figuras = next(e for e in ETAPAS if e.acao is not None)
    assert len(figuras.saidas) == 4
    assert all(s.startswith("docs/g") for s in figuras.saidas)


def test_readme_documenta_o_comando_unico():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "python -m src.rodar_tudo" in readme
    assert "streamlit run dashboard/app.py" in readme
