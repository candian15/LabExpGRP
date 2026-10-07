import json
from datetime import date

import pytest

from metricas.lead_time import lead_time_repo
from pipeline.coleta_releases import (
    coletar_releases,
    listar_commits_entre,
    listar_releases,
    releases_na_janela,
    salvar_releases_json,
)
from pipeline.github_client import ErroGitHub, NaoEncontrado

INICIO = date(2025, 1, 1)
FIM = date(2025, 12, 31)


class ClienteFalso:
    def __init__(self, releases, compares):
        self.releases = releases
        self.compares = compares
        self.chamadas = []

    def listar(self, caminho, params=None):
        self.chamadas.append(caminho)
        if caminho.endswith("/releases"):
            return list(self.releases)
        valor = self.compares[caminho.split("/compare/")[1]]
        if isinstance(valor, Exception):
            raise valor
        return list(valor)


def rel(tag, data, draft=False, prerelease=False):
    return {"tag_name": tag, "published_at": data, "draft": draft, "prerelease": prerelease}


def commit(sha, data):
    return {"sha": sha, "commit": {"author": {"date": data}}}


@pytest.fixture
def cliente():
    releases = [
        rel("v1.3", "2025-06-01T00:00:00Z"),
        rel("v1.2", "2025-04-01T00:00:00Z"),
        rel("v1.2-rc1", "2025-03-25T00:00:00Z", prerelease=True),
        rel("v1.1", "2025-03-15T00:00:00Z"),
        rel("rascunho", None, draft=True),
        rel("v1.0", "2024-12-01T00:00:00Z"),
    ]
    compares = {
        "v1.0...v1.1": [
            commit("a", "2025-03-02T00:00:00Z"),
            commit("b", "2025-03-10T00:00:00Z"),
            commit("c", "2025-03-14T00:00:00Z"),
        ],
        "v1.1...v1.2": NaoEncontrado(404, "compare"),
        "v1.2...v1.3": [],
        "v1.1...v1.2-rc1": [commit("d", "2025-03-20T00:00:00Z")],
        "v1.2-rc1...v1.2": [commit("e", "2025-03-30T00:00:00Z")],
    }
    return ClienteFalso(releases, compares)


def test_listar_releases_descarta_draft_e_ordena(cliente):
    releases = listar_releases(cliente, "o", "r")
    assert [r["tag_name"] for r in releases] == ["v1.0", "v1.1", "v1.2-rc1", "v1.2", "v1.3"]
    assert [r["prerelease"] for r in releases] == [False, False, True, False, False]


def test_releases_na_janela(cliente):
    releases = listar_releases(cliente, "o", "r")
    assert [r["tag_name"] for r in releases_na_janela(releases, INICIO, FIM)] == ["v1.1", "v1.2", "v1.3"]
    assert len(releases_na_janela(releases, INICIO, FIM, incluir_prerelease=True)) == 4
    assert len(releases_na_janela(releases, INICIO, date(2025, 3, 15))) == 1


def test_commits_entre_releases_guarda_author_date(cliente):
    commits = listar_commits_entre(cliente, "o", "r", "v1.0", "v1.1")
    assert commits[0] == {"sha": "a", "data": "2025-03-02T00:00:00Z"}
    assert len(commits) == 3


def test_tag_com_caracter_especial_e_escapada():
    c = ClienteFalso([], {"rel%231...rel%232": []})
    assert listar_commits_entre(c, "o", "r", "rel#1", "rel#2") == []


def test_coletar_releases(cliente):
    r = coletar_releases(cliente, "o", "r", INICIO, FIM)
    por_tag = {c["tag_name"]: c for c in r["comparacoes"]}
    assert list(por_tag) == ["v1.1", "v1.2", "v1.3"]
    assert por_tag["v1.1"]["anterior"] == "v1.0"
    assert por_tag["v1.2"]["status"] == "404"
    assert por_tag["v1.3"]["commits"] == []
    assert r["ignoradas_404"] == 1


def test_coleta_alimenta_lead_time(cliente):
    r = coletar_releases(cliente, "o", "r", INICIO, FIM)
    lt = lead_time_repo(r["comparacoes"])
    assert lt["lead_time_a_horas"] == 13 * 24
    assert lt["lead_time_b_horas"] == 5 * 24
    assert lt["releases_404"] == 1
    assert lt["releases_sem_commits"] == 1


def test_coletar_com_prerelease(cliente):
    r = coletar_releases(cliente, "o", "r", INICIO, FIM, incluir_prerelease=True)
    por_tag = {c["tag_name"]: c for c in r["comparacoes"]}
    assert por_tag["v1.2"]["anterior"] == "v1.2-rc1"
    assert por_tag["v1.2"]["status"] == "ok"
    assert r["ignoradas_404"] == 0


def test_primeira_release_da_historia_nao_chama_compare():
    c = ClienteFalso([rel("v1.0", "2025-02-01T00:00:00Z")], {})
    r = coletar_releases(c, "o", "r", INICIO, FIM)
    assert r["comparacoes"][0]["status"] == "primeira"
    assert len(c.chamadas) == 1


def test_release_fora_da_janela_nao_chama_compare(cliente):
    coletar_releases(cliente, "o", "r", date(2025, 5, 1), FIM)
    assert [c for c in cliente.chamadas if "/compare/" in c] == ["/repos/o/r/compare/v1.2...v1.3"]


def test_erro_que_nao_e_404_sobe():
    c = ClienteFalso(
        [rel("v1.0", "2025-02-01T00:00:00Z"), rel("v1.1", "2025-03-01T00:00:00Z")],
        {"v1.0...v1.1": ErroGitHub(500, "compare")},
    )
    with pytest.raises(ErroGitHub):
        coletar_releases(c, "o", "r", INICIO, FIM)


def test_salvar_json(cliente, tmp_path):
    r = coletar_releases(cliente, "o", "r", INICIO, FIM)
    caminho = tmp_path / "dados" / "o__r.json"
    salvar_releases_json(r, caminho)
    assert json.loads(caminho.read_text(encoding="utf-8"))["ignoradas_404"] == 1
