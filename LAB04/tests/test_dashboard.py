"""Testes do dashboard: o que ele precisa ler e montar antes de desenhar.

Não testamos a renderização do Streamlit, que depende de um servidor. Testamos o
contrato entre o dashboard e os módulos dos outros integrantes: os arquivos que ele
lê existem e têm as chaves esperadas, as figuras são geradas e o tratamento de erro
mantém a página de pé quando um módulo ainda não está pronto.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent


# ------------------------------------------------------- o que o dashboard lê
def test_cenario_tem_o_que_o_dashboard_usa():
    from src.simulacao import ler_cenario

    c = ler_cenario(RAIZ / "config" / "cenario.yaml")
    for chave in ("grupos", "n_por_grupo", "semente", "controle", "tratamento",
                  "razao_medianas_observada"):
        assert chave in c, f"o dashboard lê {chave!r} e ele não está no cenário"
    assert c["controle"] in c["grupos"] and c["tratamento"] in c["grupos"]
    for p in c["grupos"].values():
        assert {"distribuicao", "mu", "sigma", "mediana"} <= set(p)


def test_dados_reais_tem_as_colunas_do_g1():
    reais = pd.read_csv(RAIZ / "data" / "dados_reais.csv")
    assert {"grupo", "horas_ate_merge"} <= set(reais.columns)
    assert set(reais["grupo"]) == {"sem_bot", "com_bot"}
    assert (reais["horas_ate_merge"] > 0).all(), "a escala log do G1 exige valores > 0"


# ------------------------------------------------------------ as duas figuras
def test_fig_g1_e_gerada():
    from src.graficos_g1 import fig_g1, simular_para_g1
    from src.simulacao import ler_cenario

    c = ler_cenario(RAIZ / "config" / "cenario.yaml")
    reais = pd.read_csv(RAIZ / "data" / "dados_reais.csv")
    fig = fig_g1(reais, simular_para_g1(c, np.random.default_rng(c["semente"])))
    assert fig.get_axes(), "a figura do G1 saiu sem eixos"


def test_fig_g2_e_gerada():
    from src.graficos import fig_g2
    from src.simulacao import gerar_grupos, ler_cenario

    c = ler_cenario(RAIZ / "config" / "cenario.yaml")
    g = gerar_grupos(c)
    fig = fig_g2(g[c["controle"]], g[c["tratamento"]])
    assert len(fig.get_axes()) == 2, "o G2 tem um painel por teste"


# -------------------------------------------------------- tabela dos testes
def test_tabela_dos_testes_tem_as_chaves_que_o_dashboard_mostra():
    from src.simulacao import gerar_grupos, ler_cenario
    from src.testes import aplicar_testes

    c = ler_cenario(RAIZ / "config" / "cenario.yaml")
    g = gerar_grupos(c)
    resultados = aplicar_testes(g[c["controle"]], g[c["tratamento"]])
    assert len(resultados) == 2
    for r in resultados:
        assert {"teste", "estatistica", "p_valor", "efeito", "nome_efeito",
                "rejeita_h0"} <= set(r)
        assert 0 <= r["p_valor"] <= 1


def test_a_semente_torna_o_dashboard_reproduzivel():
    from src.simulacao import gerar_grupos, ler_cenario

    c = ler_cenario(RAIZ / "config" / "cenario.yaml")
    a, b = gerar_grupos(c), gerar_grupos(c)
    for nome in a:
        assert np.array_equal(a[nome], b[nome]), "duas execuções deram números diferentes"


# ------------------------------------------------- a página aguenta falha parcial
def test_o_modulo_do_dashboard_importa():
    import importlib.util

    caminho = RAIZ / "dashboard" / "app.py"
    spec = importlib.util.spec_from_file_location("dashboard_app", caminho)
    assert spec is not None and caminho.exists()


def test_links_do_cabecalho_estao_na_pagina():
    texto = (RAIZ / "dashboard" / "app.py").read_text(encoding="utf-8")
    assert "github.com/candian15/LabExpGRP" in texto, "falta o link do repositório"
    assert "projects/2" in texto, "falta o link do GitHub Projects"
    assert "DASHBOARD" in texto, "falta o campo do link do dashboard publicado"


def test_as_sete_secoes_do_enunciado_na_ordem():
    """A seção 4 do enunciado fixa os nomes e a ordem; a S02 e a entrega final só preenchem."""
    texto = (RAIZ / "dashboard" / "app.py").read_text(encoding="utf-8")
    esperado = ["1. Cenário", "2. Os dados", "3. Como os testes funcionam",
                "4. Erro tipo I", "5. Poder", "6. Dados reais", "7. Conclusão"]
    posicoes = []
    for titulo in esperado:
        marca = f'st.header("{titulo}")'
        assert marca in texto, f"falta a seção {titulo!r}"
        posicoes.append(texto.index(marca))
    assert posicoes == sorted(posicoes), "as seções estão fora da ordem do enunciado"


def test_secao_indisponivel_nao_levanta():
    """Se um módulo faltar, a seção avisa em vez de derrubar a página."""
    import sys

    sys.path.insert(0, str(RAIZ))
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "dash_app", RAIZ / "dashboard" / "app.py")
    mod = importlib.util.module_from_spec(spec)
    # executa só a definição da função, sem o corpo da página
    fonte = (RAIZ / "dashboard" / "app.py").read_text(encoding="utf-8")
    ns: dict = {}
    inicio = fonte.index("def secao_indisponivel")
    fim = fonte.index("# ------------------------------------------------------------------- cabeçalho")
    exec(compile("import streamlit as st\n" + fonte[inicio:fim], "app", "exec"), ns)
    ns["secao_indisponivel"]("G1", ImportError("modulo ausente"), "do Arthur")
