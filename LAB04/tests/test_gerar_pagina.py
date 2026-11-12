"""Testes da página publicada no GitHub Pages (``src/gerar_pagina.py``).

A página é a entrega final: é por ela que o trabalho é apresentado e corrigido. O que
testamos aqui são as exigências do enunciado que valem para ela (as sete seções na
ordem, os três links no topo, a mesma cor para cada teste, as 15 perguntas divididas
com pelo menos 4 por integrante) e as regras de apresentação em projetor (nada que
dependa de clique, nada de JavaScript, tema claro fixo).

A página é gerada uma vez só, em uma pasta temporária, e os testes leem o HTML.
"""

import re
from pathlib import Path

import pytest

from src import gerar_pagina, resultados

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    saida = tmp_path_factory.mktemp("pagina") / "index.html"
    gerar_pagina.main(saida)
    return saida.read_text(encoding="utf-8")


# ------------------------------------------------- o que o enunciado cobra da página
def test_as_sete_secoes_na_ordem_do_enunciado(html):
    esperado = ["Cenário", "Os dados", "Como os testes funcionam", "Erro tipo I",
                "Poder", "Dados reais", "Conclusão"]
    posicoes = [html.index(f"</span>{titulo}</h2>") for titulo in esperado]
    assert posicoes == sorted(posicoes), "as seções saíram fora da ordem do enunciado"


def test_os_tres_links_no_topo(html):
    topo = html[:html.index('<section id="s0"')]
    for link in (gerar_pagina.REPOSITORIO, gerar_pagina.PROJECTS, gerar_pagina.DASHBOARD):
        assert link in topo, f"falta o link {link} no topo da página"


def test_cada_grafico_tem_um_texto_de_duas_a_quatro_frases(html):
    """O enunciado pede um texto de 2 a 4 frases junto de cada gráfico, e não mais."""
    notas = re.findall(r'<div class="nota">(.*?)</div>', html, re.S)
    assert len(notas) >= 4, "falta o texto de algum gráfico"
    for nota in notas:
        frases = [f for f in re.sub(r"<[^>]+>", "", nota).split(". ") if f.strip()]
        assert 2 <= len(frases) <= 4, f"texto com {len(frases)} frases: {nota[:60]}"


def test_toda_secao_abre_com_uma_faixa_de_indicadores(html):
    """A página é um painel: cada seção mostra os números antes do texto."""
    for ident in ("s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7"):
        inicio = html.index(f'id="{ident}"')
        fim = html.index("<section", inicio + 1) if "<section" in html[inicio + 1:] else len(html)
        assert 'class="kpis"' in html[inicio:fim], f"a seção {ident} não tem faixa de números"


def test_os_cartoes_de_numero_usam_as_cores_dos_testes(html):
    """Welch e Mann-Whitney mantêm a cor deles também nos cartões."""
    assert html.count('class="tile') >= 24, "faltam cartões de indicador"
    assert '<i class="m"' in html and '<i class="w"' in html


def test_os_quatro_graficos_estao_na_pagina(html):
    assert html.count("<svg ") == 4, "a página tem G1, G2, G3 e G4"
    for descricao in ("G1:", "G2:", "G3:", "G4:"):
        assert descricao in html


# ------------------------------------------------------------ as 15 perguntas
def test_quinze_perguntas_sem_sobra_nem_falta():
    assert sorted(gerar_pagina.RESPONDE) == list(range(1, 16))


def test_cada_integrante_responde_pelo_menos_quatro():
    """Exigência da seção 5 do enunciado."""
    from collections import Counter

    por_pessoa = Counter(gerar_pagina.RESPONDE.values())
    assert set(por_pessoa) == {"Santana", "Pedro", "Arthur"}, "faltou um integrante"
    for quem, quantas in por_pessoa.items():
        assert quantas >= 4, f"{quem} responde a só {quantas} perguntas"


def test_a_pagina_mostra_quem_responde_cada_pergunta(html):
    for numero, quem, pergunta, resposta in gerar_pagina.perguntas(gerar_pagina.carregar()):
        assert f'<span class="num">{numero}</span>' in html
        assert pergunta in html, f"a pergunta {numero} não está na página"
        assert quem in html


# ------------------------------------------------------- cores e apresentação
def test_a_cor_de_cada_teste_e_a_mesma_das_figuras(html):
    """O enunciado pede a mesma cor para o mesmo teste em todos os gráficos."""
    assert gerar_pagina.COR is resultados.CORES
    for cor in resultados.CORES.values():
        assert cor in html


def test_os_grupos_nao_usam_as_cores_dos_testes():
    from src.graficos_g1 import COR_GRUPO

    assert not set(COR_GRUPO.values()) & set(resultados.CORES.values())


def test_nada_depende_de_clique_nem_de_javascript(html):
    for proibido in ("<script", "<button", "onclick", "<details", "<input"):
        assert proibido not in html, f"a página tem {proibido}, e ela é só para rolar"


def test_tema_claro_fixo(html):
    assert "prefers-color-scheme" not in html, "a página ignora o modo escuro do sistema"
    assert "color-scheme:light" in html


def test_sem_travessao(html):
    assert "—" not in html and "–" not in html


# --------------------------------------------- os números vêm mesmo dos arquivos
def test_os_numeros_saem_dos_csvs(html):
    taxas = resultados.ler_taxas(RAIZ / "resultados")
    for situacao, razao in (("real", 1.0), ("real", 0.2), ("outliers", 0.6),
                            ("bem_comportada", 0.8)):
        for teste in resultados.CORES:
            valor = gerar_pagina.taxa(taxas, situacao, razao, teste)
            assert gerar_pagina.pct(valor, 2) in html or gerar_pagina.pct(valor) in html, (
                f"{teste} em {situacao}/{razao} não aparece na página")


def test_a_pagina_e_reproduzivel(tmp_path):
    """Mesma semente, mesma página: é o que a regra de reprodutibilidade pede."""
    a, b = tmp_path / "a.html", tmp_path / "b.html"
    gerar_pagina.main(a)
    gerar_pagina.main(b)
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")


def test_o_comando_unico_gera_a_pagina():
    from src.rodar_tudo import ETAPAS

    saidas = [s for etapa in ETAPAS for s in etapa.saidas]
    assert "../index.html" in saidas, "a página não é gerada por `python -m src.rodar_tudo`"
