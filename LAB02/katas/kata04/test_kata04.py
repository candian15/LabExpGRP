from solucao import contar_eventos


def test_vazio():
    assert contar_eventos([]) == {}


def test_agrega_mesmo_tipo():
    linhas = ["0912|INFO|login", "0913|INFO|login"]
    assert contar_eventos(linhas) == {"login": 2}


def test_info_e_warn_contam():
    linhas = ["0912|INFO|login", "0914|WARN|falha"]
    assert contar_eventos(linhas) == {"login": 1, "falha": 1}


def test_debug_ignorado():
    assert contar_eventos(["0912|DEBUG|x"]) == {}


def test_malformada_ignorada():
    assert contar_eventos(["linha_ruim", "a|b"]) == {}


def test_misto():
    linhas = [
        "0912|INFO|login", "0913|DEBUG|login", "0914|WARN|login",
        "0915|INFO|logout", "ruim", "0916|WARN|falha",
    ]
    assert contar_eventos(linhas) == {"login": 2, "logout": 1, "falha": 1}
