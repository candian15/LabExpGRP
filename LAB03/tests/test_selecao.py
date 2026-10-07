"""Testes da seleção, com um cliente falso no lugar da API."""

from datetime import date

import pytest

from pipeline.selecao import avaliar, buscar_candidatos, consulta, metadados
from tests.conftest import run

INICIO, FIM = date(2026, 3, 1), date(2026, 3, 31)


class ClienteFalso:
    """Responde às chamadas que a seleção faz, sem rede, e registra os caminhos."""

    def __init__(self, workflows=1, releases=(), runs=()):
        self.workflows = workflows
        self.releases = list(releases)
        self.runs = list(runs)
        self.caminhos = []

    def get(self, caminho, params=None, usar_cache=True):
        self.caminhos.append(caminho)
        if "/actions/workflows" in caminho:
            return {"total_count": self.workflows}
        if "/actions/runs" in caminho:
            return {"total_count": len(self.runs)}
        raise AssertionError(f"caminho inesperado: {caminho}")

    def listar(self, caminho, params=None):
        self.caminhos.append(caminho)
        if "/releases" in caminho:
            return self.releases
        if "/actions/runs" in caminho:
            return self.runs
        raise AssertionError(f"caminho inesperado: {caminho}")

    def contar_por_link(self, caminho, params=None):
        self.caminhos.append(caminho)
        return 42


def repo_json(nome="octo/app", estrelas=1500, linguagem="Python", criado="2020-03-15T00:00:00Z"):
    return {
        "full_name": nome,
        "stargazers_count": estrelas,
        "language": linguagem,
        "default_branch": "main",
        "created_at": criado,
    }


def release(dia, tag="v1.0", prerelease=False, draft=False):
    return {
        "tag_name": tag,
        "published_at": f"2026-03-{dia:02d}T12:00:00Z",
        "prerelease": prerelease,
        "draft": draft,
        "html_url": f"https://github.com/octo/app/releases/tag/{tag}",
    }


def releases(n, prerelease=False):
    return [release(i + 1, tag=f"v1.{i}", prerelease=prerelease) for i in range(n)]


def runs_validos_falsos(n, conclusion="success"):
    return [run(f"{h // 60:02d}:{h % 60:02d}", conclusion, id_=h + 1) for h in range(n)]


def test_metadados_vem_da_busca_sem_chamada_extra():
    meta = metadados(repo_json(), referencia=date(2026, 3, 31))
    assert meta["repo"] == "octo/app"
    assert meta["estrelas"] == 1500
    assert meta["linguagem"] == "Python"
    assert meta["default_branch"] == "main"
    assert meta["criado_em"] == "2020-03-15"
    assert meta["idade_anos"] == pytest.approx(6.04, abs=0.01)


def test_consulta_fatia_por_estrelas_e_linguagem():
    assert consulta("1000..2000") == "stars:1000..2000"
    assert consulta(">1000", "Python") == "stars:>1000 language:Python"


def test_sem_actions_descarta_antes_de_gastar_outras_chamadas():
    gh = ClienteFalso(workflows=0)
    linha = avaliar(gh, repo_json(), INICIO, FIM)
    assert linha["motivo_descarte"] == "sem_actions"
    assert gh.caminhos == ["/repos/octo/app/actions/workflows"]


def test_poucas_releases_descarta_antes_de_coletar_runs():
    gh = ClienteFalso(releases=releases(4), runs=runs_validos_falsos(100))
    linha = avaliar(gh, repo_json(), INICIO, FIM)
    assert linha["motivo_descarte"] == "poucas_releases"
    assert linha["n_releases"] == 4
    assert not any("/actions/runs" in c for c in gh.caminhos)


def test_prerelease_nao_conta_como_deploy_na_definicao_principal():
    gh = ClienteFalso(releases=releases(6, prerelease=True), runs=runs_validos_falsos(100))
    linha = avaliar(gh, repo_json(), INICIO, FIM)
    assert (linha["n_releases"], linha["motivo_descarte"]) == (0, "poucas_releases")


def test_release_fora_da_janela_nao_conta():
    fora = [release(1, tag=f"v2.{i}") for i in range(6)]
    for r in fora:
        r["published_at"] = "2025-01-10T12:00:00Z"
    gh = ClienteFalso(releases=fora, runs=runs_validos_falsos(100))
    assert avaliar(gh, repo_json(), INICIO, FIM)["motivo_descarte"] == "poucas_releases"


def test_runs_ignorados_nao_entram_no_minimo_de_50():
    # 49 válidos + 10 cancelados: o repositório continua abaixo do corte.
    runs = runs_validos_falsos(49) + [run("23:00", "cancelled", id_=900 + i) for i in range(10)]
    gh = ClienteFalso(releases=releases(6), runs=runs)
    linha = avaliar(gh, repo_json(), INICIO, FIM)
    assert linha["motivo_descarte"] == "poucos_runs"
    assert linha["n_runs_validos"] == 49


def test_repositorio_aprovado_traz_runs_e_contribuidores():
    gh = ClienteFalso(releases=releases(6), runs=runs_validos_falsos(60))
    linha = avaliar(gh, repo_json(), INICIO, FIM, contribuidores=True)
    assert linha["motivo_descarte"] == ""
    assert (linha["n_releases"], linha["n_runs_validos"]) == (6, 60)
    assert linha["contribuidores"] == 42
    assert len(linha["runs"]) == 60


class BuscaFalsa:
    """Cliente que devolve páginas de busca prontas, por consulta."""

    def __init__(self, por_consulta):
        self.por_consulta = por_consulta
        self.consultas = []

    def paginar(self, caminho, params=None):
        self.consultas.append(params["q"])
        itens = self.por_consulta.get(params["q"], [])
        yield {"total_count": len(itens), "items": itens}


def test_busca_junta_faixas_sem_repetir_e_ordena_por_estrelas():
    a, b = repo_json("a/a", estrelas=1200), repo_json("b/b", estrelas=9000)
    gh = BuscaFalsa({"stars:1000..2000": [a], "stars:>2000": [b, a]})
    achados = buscar_candidatos(gh, ["1000..2000", ">2000"])
    assert [r["full_name"] for r in achados] == ["b/b", "a/a"]
    assert gh.consultas == ["stars:1000..2000", "stars:>2000"]


def test_busca_respeita_o_teto_de_resultados_por_consulta():
    muitos = [repo_json(f"o/r{i}", estrelas=i) for i in range(10)]
    gh = BuscaFalsa({"stars:>1000": muitos})
    assert len(buscar_candidatos(gh, [">1000"], limite_por_consulta=3)) == 3
