from solucao import escalonar


def test_uma_tarefa():
    assert escalonar({"a": {"deps": [], "prioridade": 1}}) == ["a"]


def test_dependencia_simples():
    t = {
        "a": {"deps": [], "prioridade": 1},
        "b": {"deps": ["a"], "prioridade": 5},
    }
    assert escalonar(t) == ["a", "b"]


def test_desempate_por_prioridade():
    t = {
        "a": {"deps": [], "prioridade": 1},
        "b": {"deps": [], "prioridade": 9},
    }
    assert escalonar(t) == ["b", "a"]


def test_desempate_alfabetico():
    t = {
        "y": {"deps": [], "prioridade": 3},
        "x": {"deps": [], "prioridade": 3},
    }
    assert escalonar(t) == ["x", "y"]


def test_ciclo_retorna_vazio():
    t = {
        "a": {"deps": ["b"], "prioridade": 1},
        "b": {"deps": ["a"], "prioridade": 1},
    }
    assert escalonar(t) == []


def test_prioridade_respeita_dependencia():
    # c tem prioridade alta mas depende de a e b
    t = {
        "a": {"deps": [], "prioridade": 1},
        "b": {"deps": [], "prioridade": 2},
        "c": {"deps": ["a", "b"], "prioridade": 9},
    }
    assert escalonar(t) == ["b", "a", "c"]


def test_cadeia_com_ramos():
    t = {
        "setup": {"deps": [], "prioridade": 5},
        "build": {"deps": ["setup"], "prioridade": 3},
        "lint": {"deps": ["setup"], "prioridade": 8},
        "test": {"deps": ["build", "lint"], "prioridade": 1},
    }
    assert escalonar(t) == ["setup", "lint", "build", "test"]
