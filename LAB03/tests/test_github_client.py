"""Testes do cliente HTTP sem acessar a internet (sessão falsa)."""

import pytest
import requests

from pipeline.github_client import GitHubClient, NaoEncontrado, extrair_itens


class RespostaFalsa:
    def __init__(self, status=200, dados=None, headers=None, links=None):
        self.status_code = status
        self._dados = dados
        self.headers = headers or {}
        self.links = links or {}
        self.text = str(dados)

    def json(self):
        return self._dados


class SessaoFalsa:
    """Devolve respostas em sequência e registra as URLs pedidas."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.urls = []
        self.headers = {}

    def get(self, url, timeout=None):
        self.urls.append(url)
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def novo_cliente(tmp_path):
    def fabrica(respostas, agora=1000.0):
        sessao = SessaoFalsa(respostas)
        esperas = []
        gh = GitHubClient(
            token="token-teste",
            cache_dir=tmp_path / "cache",
            session=sessao,
            dormir=esperas.append,
            agora=lambda: agora,
        )
        return gh, sessao, esperas

    return fabrica


def test_exige_token(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        GitHubClient(cache_dir=tmp_path)


def test_le_token_do_ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_TOKEN", "abc")
    gh = GitHubClient(cache_dir=tmp_path, session=SessaoFalsa([]))
    assert gh.session.headers["Authorization"] == "Bearer abc"


def test_cache_evita_segunda_chamada(novo_cliente):
    gh, sessao, _ = novo_cliente([RespostaFalsa(dados={"default_branch": "main"})])
    assert gh.get("/repos/a/b")["default_branch"] == "main"
    assert gh.get("/repos/a/b")["default_branch"] == "main"
    assert len(sessao.urls) == 1
    assert gh.acertos_cache == 1


def test_cache_sobrevive_a_novo_cliente(tmp_path):
    """Retomada: um processo novo lê o que o anterior gravou."""
    s1 = SessaoFalsa([RespostaFalsa(dados=[1, 2])])
    GitHubClient(token="t", cache_dir=tmp_path, session=s1).get("/x")
    s2 = SessaoFalsa([])  # se tentar acessar a rede, quebra
    assert GitHubClient(token="t", cache_dir=tmp_path, session=s2).get("/x") == [1, 2]
    assert s2.urls == []


def test_cache_corrompido_refaz_chamada(novo_cliente):
    gh, sessao, _ = novo_cliente([RespostaFalsa(dados=1), RespostaFalsa(dados=2)])
    gh.get("/x")
    arq = gh._arquivo_cache(gh._montar_url("/x", None))
    arq.write_text("{quebrado")
    assert gh.get("/x") == 2
    assert len(sessao.urls) == 2


def test_paginacao_segue_link(novo_cliente):
    gh, sessao, _ = novo_cliente(
        [
            RespostaFalsa(dados={"total_count": 3, "workflow_runs": [1, 2]}, links={"next": {"url": "https://api.github.com/p2"}}),
            RespostaFalsa(dados={"total_count": 3, "workflow_runs": [3]}),
        ]
    )
    assert gh.listar("/repos/a/b/actions/runs") == [1, 2, 3]
    assert sessao.urls[1] == "https://api.github.com/p2"
    assert "per_page=100" in sessao.urls[0]


def test_backoff_exponencial_em_5xx(novo_cliente):
    gh, sessao, esperas = novo_cliente(
        [RespostaFalsa(502), RespostaFalsa(503), RespostaFalsa(500), RespostaFalsa(dados="ok")]
    )
    assert gh.get("/x") == "ok"
    assert esperas == [1, 2, 4]


def test_5xx_persistente_desiste(novo_cliente):
    gh, _, esperas = novo_cliente([RespostaFalsa(500)] * 6)
    with pytest.raises(Exception):
        gh.get("/x")
    assert esperas == [1, 2, 4, 8, 16]


def test_erro_de_rede_tambem_tem_backoff(novo_cliente):
    gh, _, esperas = novo_cliente([requests.ConnectionError("caiu"), RespostaFalsa(dados="ok")])
    assert gh.get("/x") == "ok"
    assert esperas == [1]


def test_espera_reset_quando_cota_acaba(novo_cliente):
    sem_cota = RespostaFalsa(403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1100"})
    gh, sessao, esperas = novo_cliente([sem_cota, RespostaFalsa(dados="ok")], agora=1000.0)
    assert gh.get("/x") == "ok"
    assert esperas == [102]  # 100s até o reset + 2s de folga
    assert len(sessao.urls) == 2


def test_ultima_resposta_da_cota_e_aproveitada(novo_cliente):
    ultima = RespostaFalsa(200, dados="ok", headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1010"})
    gh, sessao, esperas = novo_cliente([ultima], agora=1000.0)
    assert gh.get("/x") == "ok"
    assert esperas == [12]
    assert len(sessao.urls) == 1


def test_rate_limit_secundario_usa_retry_after(novo_cliente):
    gh, _, esperas = novo_cliente([RespostaFalsa(403, headers={"Retry-After": "30"}), RespostaFalsa(dados="ok")])
    assert gh.get("/x") == "ok"
    assert esperas == [31]


def test_404_levanta_e_fica_em_cache(novo_cliente):
    gh, sessao, _ = novo_cliente([RespostaFalsa(404)])
    with pytest.raises(NaoEncontrado):
        gh.get("/repos/a/b/compare/v1...v2")
    with pytest.raises(NaoEncontrado):
        gh.get("/repos/a/b/compare/v1...v2")
    assert len(sessao.urls) == 1


def test_contar_por_link(novo_cliente):
    gh, sessao, _ = novo_cliente(
        [RespostaFalsa(dados=[{}], links={"last": {"url": "https://api.github.com/x?per_page=1&page=57"}})]
    )
    assert gh.contar_por_link("/repos/a/b/contributors", {"anon": "true"}) == 57
    assert "per_page=1" in sessao.urls[0]


def test_contar_por_link_sem_paginas(novo_cliente):
    gh, _, _ = novo_cliente([RespostaFalsa(dados=[{}])])
    assert gh.contar_por_link("/repos/a/b/contributors") == 1


def test_extrair_itens():
    assert extrair_itens([1]) == [1]
    assert extrair_itens({"items": [2]}) == [2]
    assert extrair_itens({"commits": [3], "total_commits": 1}) == [3]
    assert extrair_itens(None) == []
    assert extrair_itens({"x": 1}) == []
