from solucao import deduplicar


def test_vazio():
    assert deduplicar([]) == []


def test_sem_duplicatas():
    assert deduplicar(["Ana", "Bia"]) == ["Ana", "Bia"]


def test_espacos_e_caixa():
    assert deduplicar(["Ana Lima", "ana  lima", "  Ana Lima "]) == ["Ana Lima"]


def test_abreviacao_tratamento():
    assert deduplicar(["Dr House", "doutor house"]) == ["Dr House"]


def test_preserva_primeira_ocorrencia():
    entrada = ["ana lima", "Ana Lima"]
    assert deduplicar(entrada) == ["ana lima"]


def test_misto_ordem():
    entrada = ["Bia", "  bia ", "Sra Silva", "senhora silva", "Bia"]
    assert deduplicar(entrada) == ["Bia", "Sra Silva"]
