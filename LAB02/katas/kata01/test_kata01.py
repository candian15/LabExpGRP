from solucao import normalizar_agenda


def test_vazio():
    assert normalizar_agenda([]) == []


def test_um_intervalo():
    assert normalizar_agenda([(10, 20)]) == [(10, 20)]


def test_sem_sobreposicao_ordena():
    assert normalizar_agenda([(60, 90), (0, 30)]) == [(0, 30), (60, 90)]


def test_sobreposicao_simples():
    assert normalizar_agenda([(0, 30), (20, 50)]) == [(0, 50)]


def test_bordas_tocam_mesclam():
    assert normalizar_agenda([(0, 30), (30, 60)]) == [(0, 60)]


def test_varios_fora_de_ordem():
    entrada = [(60, 90), (0, 30), (20, 50), (85, 100)]
    assert normalizar_agenda(entrada) == [(0, 50), (60, 100)]
