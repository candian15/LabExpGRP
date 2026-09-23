def normalizar_agenda(intervalos):
    """Mescla intervalos de agenda sobrepostos ou adjacentes.

    Ver especificacao do kata 1 em katas.json (campo "especificacao").
    Intervalos que apenas se tocam na borda tambem sao mesclados.
    """
    if not intervalos:
        return []

    ordenados = sorted(intervalos, key=lambda par: (par[0], par[1]))
    mesclados = [tuple(ordenados[0])]

    for inicio, fim in ordenados[1:]:
        ultimo_inicio, ultimo_fim = mesclados[-1]
        if inicio <= ultimo_fim:
            mesclados[-1] = (ultimo_inicio, max(ultimo_fim, fim))
        else:
            mesclados.append((inicio, fim))

    return mesclados
