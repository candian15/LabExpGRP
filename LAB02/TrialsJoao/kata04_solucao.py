def contar_eventos(linhas):
    """Agrega contagem de eventos por tipo a partir de linhas de log.

    Ver a especificacao do kata 4 em katas.json (campo "especificacao").
    """
    eventos = {}
    for linha in linhas:
        lista = linha.split("|")
        if len(lista) != 3:
            continue
        if lista[1].lower() not in ("warn","info"):
            continue
        contagem_atual = eventos.get(lista[2])
        if contagem_atual is None:
            eventos[lista[2]] = 1
        else:
            eventos[lista[2]] = contagem_atual + 1

    return eventos
