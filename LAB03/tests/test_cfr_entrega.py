from datetime import date

import pytest

from metricas.cfr_entrega import (
    HEURISTICAS,
    assunto,
    cfr_entrega,
    classificar_releases,
    commits_substantivos,
    eh_correcao,
    eh_corretiva,
    fracao_correcoes,
    tem_correcao_substantiva,
    so_patch,
    so_secao_de_correcao,
    versao_semver,
)

FIM = date(2026, 9, 30)


def commit(msg):
    return {"sha": "x", "data": "2026-05-01T00:00:00Z", "message": msg}


def item(tag, data, anterior, msgs=(), status="ok", body=""):
    return {
        "tag_name": tag,
        "published_at": f"{data}T12:00:00Z",
        "anterior": anterior,
        "status": status,
        "body": body,
        "commits": [commit(m) for m in msgs],
    }


# ------------------------------------------------------------------ sinais simples
@pytest.mark.parametrize(
    "tag,esperado",
    [("v2.3.1", (2, 3, 1)), ("2.3.1", (2, 3, 1)), ("release-1.0.12", (1, 0, 12)), ("v2.3", None), ("nightly", None), (None, None)],
)
def test_versao_semver(tag, esperado):
    assert versao_semver(tag) == esperado


@pytest.mark.parametrize(
    "anterior,atual,esperado",
    [
        ("v2.3.0", "v2.3.1", True),
        ("v2.3.1", "v2.3.5", True),
        ("v2.3.0", "v2.4.0", False),
        ("v2.3.0", "v3.0.0", False),
        ("v2.3.1", "v2.3.0", False),  # patch voltou: não é correção
        ("v2.3", "v2.3.1", False),  # sem SemVer completo
        (None, "v2.3.1", False),
    ],
)
def test_so_patch(anterior, atual, esperado):
    assert so_patch(anterior, atual) is esperado


@pytest.mark.parametrize(
    "msg,esperado",
    [
        ("fix: crash ao abrir arquivo", True),
        ("Fix #123 null pointer", True),
        ("Fixes a bug in parser", True),
        ("hotfix: build quebrado", True),
        ('Revert "Add feature X"', True),
        ("feat: novo botão", False),
        ("add prefix to names", False),  # 'prefix' não é 'fix'
        ("update fixtures", False),  # 'fixtures' não é 'fix'
        ("feat: add x\n\nfixes #12", False),  # só o assunto conta
        ("", False),
        (None, False),
    ],
)
def test_eh_correcao(msg, esperado):
    assert eh_correcao(msg) is esperado


def test_assunto_pega_a_primeira_linha():
    assert assunto("  linha 1\nlinha 2") == "linha 1"
    assert assunto(None) == ""


def test_fracao_correcoes():
    assert fracao_correcoes([]) == 0.0
    assert fracao_correcoes([commit("fix: a"), commit("feat: b"), commit("revert c"), commit("docs")]) == 0.5


# ------------------------------------------------------------ classificação / heurística
def test_primeira_release_nunca_e_corretiva():
    assert eh_corretiva(item("v1.0.1", "2026-01-01", None, ["fix: a"])) is False


def test_v1_patch_ou_mensagem():
    assert eh_corretiva(item("v2.3.1", "2026-05-12", "v2.3.0", ["docs"]), "v1") is True  # só patch
    assert eh_corretiva(item("v2.4.0", "2026-05-12", "v2.3.0", ["feat", "fix: b"]), "v1") is True  # tem fix
    assert eh_corretiva(item("v2.4.0", "2026-05-12", "v2.3.0", ["feat: x"]), "v1") is False


def test_v2_exige_metade_de_correcoes_quando_nao_e_patch():
    assert eh_corretiva(item("v2.4.0", "2026-05-12", "v2.3.0", ["feat", "fix: b"]), "v2") is True  # 1/2
    assert eh_corretiva(item("v2.4.0", "2026-05-12", "v2.3.0", ["feat", "feat", "fix: b"]), "v2") is False  # 1/3
    assert eh_corretiva(item("v2.3.1", "2026-05-12", "v2.3.0", ["docs"]), "v2") is True  # patch


def test_v3_patch_sem_correcao_nao_basta():
    assert eh_corretiva(item("v2.3.1", "2026-05-12", "v2.3.0", ["chore: deps"]), "v3") is False
    assert eh_corretiva(item("v2.3.1", "2026-05-12", "v2.3.0", ["chore", "fix: a"]), "v3") is True
    assert eh_corretiva(item("v2.4.0", "2026-05-12", "v2.3.0", ["fix: a", "fix: b"]), "v3") is True


def test_compare_404_so_usa_a_versao():
    c = item("v2.3.1", "2026-05-12", "v2.3.0", status="404")
    assert eh_corretiva(c, "v1") is True
    assert eh_corretiva(item("v2.4.0", "2026-05-12", "v2.3.0", status="404"), "v1") is False


def test_versao_desconhecida():
    with pytest.raises(ValueError):
        eh_corretiva(item("v1.0.1", "2026-05-12", "v1.0.0"), "v99")


def test_classificar_releases_ordena_por_data():
    comps = [
        item("v2.3.1", "2026-05-12", "v2.3.0", ["fix: a"]),
        item("v2.3.0", "2026-05-10", "v2.2.0", ["feat"]),
    ]
    out = classificar_releases(comps)
    assert [r["tag_name"] for r in out] == ["v2.3.0", "v2.3.1"]
    assert [r["corretiva"] for r in out] == [False, True]


def test_todas_as_versoes_registradas_rodam():
    c = item("v1.0.1", "2026-05-12", "v1.0.0", ["fix: a"])
    for versao in HEURISTICAS:
        assert isinstance(eh_corretiva(c, versao), bool)


# ----------------------------------------------------------------------------- CFR (b)
def test_exemplo_do_enunciado():
    """v2.3.0 (10/05) -> v2.3.1 (12/05, patch + fix): v2.3.0 falhou.
    v2.4.0 (01/06) -> v2.5.0 (20/06): v2.4.0 não falhou."""
    comps = [
        item("v2.3.0", "2026-05-10", "v2.2.0", ["feat: algo"]),
        item("v2.3.1", "2026-05-12", "v2.3.0", ["fix: crash ao abrir arquivo"]),
        item("v2.4.0", "2026-06-01", "v2.3.1", ["feat: y"]),
        item("v2.5.0", "2026-06-20", "v2.4.0", ["feat: z"]),
    ]
    r = cfr_entrega(comps, FIM)
    assert r["n_avaliadas"] == 4
    assert r["n_falhas"] == 1  # só v2.3.0
    assert r["cfr_entrega"] == 0.25
    assert r["n_corretivas"] == 1


def test_correcao_fora_dos_7_dias_nao_conta():
    comps = [
        item("v1.0.0", "2026-03-01", "v0.9.0", ["feat"]),
        item("v1.0.1", "2026-03-09", "v1.0.0", ["fix: a"]),  # 8 dias depois
    ]
    r = cfr_entrega(comps, FIM)
    assert r["n_falhas"] == 0
    assert r["cfr_entrega"] == 0.0


def test_correcao_exatamente_em_7_dias_conta():
    comps = [
        item("v1.0.0", "2026-03-01", "v0.9.0", ["feat"]),
        item("v1.0.1", "2026-03-08", "v1.0.0", ["fix: a"]),
    ]
    assert cfr_entrega(comps, FIM)["n_falhas"] == 1


def test_censura_dos_ultimos_7_dias_da_janela():
    comps = [
        item("v1.0.0", "2026-03-01", "v0.9.0", ["feat"]),
        item("v1.1.0", "2026-09-20", "v1.0.0", ["feat"]),  # avaliável (mais de 7 dias antes do fim)
        item("v1.1.1", "2026-09-26", "v1.1.0", ["fix: a"]),  # nos últimos 7 dias: censurada
    ]
    r = cfr_entrega(comps, FIM)
    assert r["n_censuradas"] == 1
    assert r["n_avaliadas"] == 2
    assert r["n_falhas"] == 1  # v1.1.0 foi seguida da correção v1.1.1
    assert r["cfr_entrega"] == 0.5


def test_ultima_release_avaliavel_sem_seguinte_nao_falha():
    comps = [item("v1.0.0", "2026-03-01", "v0.9.0", ["feat"])]
    r = cfr_entrega(comps, FIM)
    assert (r["n_avaliadas"], r["n_falhas"], r["cfr_entrega"]) == (1, 0, 0.0)


def test_repositorio_com_uma_unica_release_na_historia():
    comps = [item("v1.0.0", "2026-03-01", None, status="primeira")]
    r = cfr_entrega(comps, FIM)
    assert r["cfr_entrega"] == 0.0
    assert r["n_corretivas"] == 0


def test_tudo_censurado_devolve_none():
    comps = [item("v1.0.0", "2026-09-28", "v0.9.0", ["feat"])]
    r = cfr_entrega(comps, FIM)
    assert r["cfr_entrega"] is None
    assert r["n_avaliadas"] == 0
    assert r["n_censuradas"] == 1


def test_sem_releases():
    r = cfr_entrega([], FIM)
    assert r["cfr_entrega"] is None
    assert r["n_avaliadas"] == r["n_censuradas"] == 0


def test_limite_da_censura_e_inclusivo_no_fim_da_janela():
    # publicada às 12:00 de 23/09: +7 dias = 30/09 12:00, ainda dentro do fim (30/09 inclusivo)
    comps = [item("v1.0.0", "2026-09-23", "v0.9.0", ["feat"])]
    assert cfr_entrega(comps, FIM)["n_avaliadas"] == 1
    # publicada em 24/09: +7 dias passa do fim da janela
    comps = [item("v1.0.0", "2026-09-24", "v0.9.0", ["feat"])]
    assert cfr_entrega(comps, FIM)["n_censuradas"] == 1


def test_heuristica_muda_o_resultado():
    comps = [
        item("v1.0.0", "2026-03-01", "v0.9.0", ["feat"]),
        item("v1.1.0", "2026-03-03", "v1.0.0", ["feat", "feat", "fix: a"]),  # 1/3 de fix
    ]
    assert cfr_entrega(comps, FIM, versao="v1")["n_falhas"] == 1
    assert cfr_entrega(comps, FIM, versao="v2")["n_falhas"] == 0


# ------------------------------------------------------------------ sinais da v4
def test_commits_substantivos_tira_manutencao_e_dependencias():
    commits = [commit(m) for m in (
        "fix: corrige o parser", "chore: limpa imports", "ci: ajusta o workflow",
        "build(deps): bump lodash from 4.17.20 to 4.17.21", "docs: README",
        "feat: nova opção", "Merge pull request #12",
    )]
    assert [assunto(c["message"]) for c in commits_substantivos(commits)] == [
        "fix: corrige o parser", "feat: nova opção"]


def test_tem_correcao_substantiva_ignora_o_ruido():
    assert tem_correcao_substantiva([commit("fix: a"), commit("chore: b")]) is True
    # o "fix" está só num commit de manutenção: não conta
    assert tem_correcao_substantiva([commit("chore: fix lockfile"), commit("docs: x")]) is False
    assert tem_correcao_substantiva([]) is False


@pytest.mark.parametrize("body,esperado", [
    ("## Bug Fixes\n- corrige o parser", True),
    ("### Fixed\n- trava ao abrir", True),
    ("## Bug Fixes\n- a\n## Features\n- b", False),      # tem novidade junto
    ("## Features\n- nova tela", False),
    ("", False),
    (None, False),
])
def test_so_secao_de_correcao(body, esperado):
    assert so_secao_de_correcao(body) is esperado


# ------------------------------------------------------------------------- v4
def test_v4_release_notes_so_de_correcao_bastam():
    # nem é patch, mas as notas só falam de correção
    c = item("v3.0.0", "2026-05-12", "v2.9.0", ["feat: x"], body="## Bug Fixes\n- y")
    assert eh_corretiva(c, "v4") is True


def test_v4_notas_com_novidade_nao_contam():
    c = item("v3.0.0", "2026-05-12", "v2.9.0", ["feat: x"],
             body="## Bug Fixes\n- a\n## Features\n- b")
    assert eh_corretiva(c, "v4") is False


def test_v4_patch_sozinho_nao_basta():
    # era o que a v1 fazia e gerava os falsos positivos
    c = item("v2.3.1", "2026-05-12", "v2.3.0", ["chore: bump deps", "docs: readme"])
    assert eh_corretiva(c, "v4") is False
    assert eh_corretiva(c, "v1") is True


def test_v4_patch_com_alguma_correcao_real():
    c = item("v2.3.1", "2026-05-12", "v2.3.0", ["fix: a", "feat: b", "chore: deps"])
    assert eh_corretiva(c, "v4") is True


def test_v4_patch_so_com_manutencao_nao_conta():
    # era o caso que mais gerava falso positivo na v1
    c = item("v2.3.1", "2026-05-12", "v2.3.0", ["chore(deps): bump lodash", "ci: cache"])
    assert eh_corretiva(c, "v4") is False


def test_v4_primeira_release_nunca_e_corretiva():
    assert eh_corretiva(item("v1.0.0", "2026-01-01", None, body="## Bug Fixes\n- x"), "v4") is False


def test_v4_esta_registrada():
    assert "v4" in HEURISTICAS
