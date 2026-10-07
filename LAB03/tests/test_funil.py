import csv

from pipeline import funil


def avaliacao(repo, motivo=""):
    return {"repo": repo, "motivo_descarte": motivo}


AVALIACOES = [
    avaliacao("a/1"),
    avaliacao("a/2"),
    avaliacao("b/1", "sem_actions"),
    avaliacao("b/2", "sem_actions"),
    avaliacao("b/3", "sem_actions"),
    avaliacao("c/1", "poucas_releases"),
    avaliacao("c/2", "poucas_releases"),
    avaliacao("d/1", "poucos_runs"),
    avaliacao("e/1", "erro"),
]


def test_cada_etapa_mostra_quantos_sobraram():
    tabela = funil.linhas(AVALIACOES)
    assert [(l["etapa"].split(" (")[0], l["restantes"], l["descartados"]) for l in tabela] == [
        ("candidatos da busca", 9, ""),
        ("usam GitHub Actions", 6, 3),
        ("≥ 5 releases publicadas na janela", 4, 2),
        ("≥ 50 workflow runs válidos na janela", 3, 1),
        ("coleta concluída sem erro", 2, 1),
        ("amostra final", 2, ""),
    ]


def test_amostra_final_bate_com_quem_nao_foi_descartado():
    tabela = funil.linhas(AVALIACOES)
    aprovados = sum(1 for a in AVALIACOES if not a["motivo_descarte"])
    assert tabela[-1]["restantes"] == aprovados


def test_criterios_seguem_os_minimos_configurados():
    tabela = funil.linhas(AVALIACOES, min_releases=10, min_runs=100)
    etapas = [l["etapa"] for l in tabela]
    assert "≥ 10 releases publicadas na janela" in etapas
    assert "≥ 100 workflow runs válidos na janela" in etapas


def test_candidatos_nao_avaliados_aparecem_como_etapa():
    tabela = funil.linhas(AVALIACOES, n_candidatos=50)
    assert tabela[0]["restantes"] == 50
    assert (tabela[1]["etapa"], tabela[1]["descartados"], tabela[1]["restantes"]) == ("avaliados", 41, 9)
    assert tabela[-1]["restantes"] == 2


def test_toda_etapa_de_filtro_explica_o_descarte():
    tabela = funil.linhas(AVALIACOES)
    assert all(l["motivo_do_descarte"] for l in tabela[1:-1])
    # As linhas de resumo (total da busca e amostra final) não descartam nada.
    assert (tabela[0]["motivo_do_descarte"], tabela[-1]["motivo_do_descarte"]) == ("", "")


def test_csv_tem_uma_linha_por_etapa(tmp_path):
    tabela = funil.linhas(AVALIACOES)
    caminho = tmp_path / "saida" / "funil.csv"
    funil.salvar_csv(tabela, funil.CAMPOS, caminho)
    with caminho.open(encoding="utf-8") as f:
        lido = list(csv.DictReader(f))
    assert len(lido) == len(tabela)
    assert lido[0]["restantes"] == "9"
    assert lido[1]["motivo_do_descarte"] == "total_count = 0 em /actions/workflows"


def test_csv_ignora_colunas_extras_e_preenche_as_que_faltam(tmp_path):
    caminho = tmp_path / "repositorios.csv"
    funil.salvar_csv([{"repo": "a/1", "runs": [1, 2, 3]}], ["repo", "dora"], caminho)
    assert caminho.read_text(encoding="utf-8").splitlines() == ["repo,dora", "a/1,"]
