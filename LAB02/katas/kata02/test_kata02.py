from solucao import validar_senha


def test_ok():
    assert validar_senha("Senha9x7y2z") == "ok"


def test_comprimento():
    assert validar_senha("curta1A") == "comprimento"


def test_digitos():
    assert validar_senha("Abcdefghij") == "digitos"


def test_maiuscula():
    assert validar_senha("senhaxy789q") == "maiuscula"


def test_maiuscula_precede_sequencia():
    # sem maiuscula E com "123": a regra de maiuscula vem antes
    assert validar_senha("senhax1234q") == "maiuscula"


def test_simbolo_proibido():
    assert validar_senha("Senha 9x7y2") == "simbolo_proibido"


def test_sequencia():
    assert validar_senha("Abcdef1234z") == "sequencia"
