from solucao import calcular_troco


def test_valor_zero():
    assert calcular_troco(0, [2, 5]) == 0


def test_uma_moeda_exata():
    assert calcular_troco(4, [1, 3, 4]) == 1


def test_guloso_falha_precisa_otimo():
    assert calcular_troco(6, [1, 3, 4]) == 2


def test_impossivel():
    assert calcular_troco(3, [2]) == -1


def test_multiplas_da_mesma():
    assert calcular_troco(9, [3]) == 3


def test_combinacao():
    assert calcular_troco(11, [1, 5, 6]) == 2
