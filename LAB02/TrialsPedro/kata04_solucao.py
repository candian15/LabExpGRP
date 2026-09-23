NIVEIS_CONTABILIZADOS = frozenset({"INFO", "WARN"})
CAMPOS_ESPERADOS = 3


def contar_eventos(linhas):
    """Conta eventos por TIPO em linhas 'TIMESTAMP|NIVEL|TIPO'.

    Ver especificacao do kata 4 em katas.json (campo "especificacao").
    Linhas malformadas e niveis fora de INFO/WARN sao ignorados.
    """
    contagem = {}

    for linha in linhas:
        campos = linha.split("|")
        if len(campos) != CAMPOS_ESPERADOS:
            continue

        _, nivel, tipo = campos
        if nivel not in NIVEIS_CONTABILIZADOS:
            continue

        contagem[tipo] = contagem.get(tipo, 0) + 1

    return contagem
