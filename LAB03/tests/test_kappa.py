import pytest

from validacao.kappa_fleiss import calcular, interpretar, kappa


def test_caso_calculado_a_mao():
    """4 itens, 3 avaliadores: (s,s,s) (n,n,n) (s,s,n) (s,n,n).

    P̄ = (1 + 1 + 1/3 + 1/3) / 4 = 2/3; P_e = 0,5² + 0,5² = 1/2.
    κ = (2/3 − 1/2) / (1 − 1/2) = 1/3.
    """
    linhas = [["sim", "sim", "sim"], ["nao", "nao", "nao"], ["sim", "sim", "nao"], ["sim", "nao", "nao"]]
    assert kappa(linhas) == pytest.approx(1 / 3)


def test_concordancia_perfeita():
    assert kappa([["biblioteca"] * 3, ["cli"] * 3]) == pytest.approx(1.0)


def test_kappa_indefinido_quando_todos_iguais():
    assert kappa([["sim"] * 3, ["sim"] * 3]) is None


@pytest.mark.parametrize("k, esperado", [
    (-0.1, "pobre"), (0.10, "leve"), (0.30, "razoável"), (0.50, "moderada"),
    (0.70, "substancial"), (0.90, "quase perfeita"), (None, "indefinido"),
])
def test_interpretacao_landis_koch(k, esperado):
    assert interpretar(k) == esperado


def test_calcular_exclui_itens_em_branco():
    def rot(corretivas):
        return {"tipo_projeto": {}, "entregas_reais": {},
                "corretiva": {("o/r", f"v{i}"): v for i, v in enumerate(corretivas)}}

    rotulos = {"artur": rot(["sim", "nao", "sim", "sim", "sim"]),
               "joao": rot(["sim", "nao", "sim", "nao", None]),
               "pedro": rot(["sim", "nao", "nao", "nao", "sim"])}
    corretiva = next(r for r in calcular(rotulos) if r["dimensao"] == "corretiva")
    assert corretiva["n_itens"] == 4
    assert corretiva["n_excluidos"] == 1
    assert corretiva["kappa"] == pytest.approx(1 / 3, abs=1e-4)
