def normalizar_agenda(intervalos):
    """Mescla intervalos de horário sobrepostos ou que se tocam na borda.

    Ver a especificacao do kata 1 em katas.json (campo "especificacao").
    """
    if not intervalos:
        return []

    ordenados = sorted(intervalos)
    mesclados = [ordenados[0]]

    for inicio, fim in ordenados[1:]:
        ultimo_inicio, ultimo_fim = mesclados[-1]
        if inicio <= ultimo_fim:
            # Sobrepoe ou toca na borda (inicio == ultimo_fim): mescla.
            mesclados[-1] = (ultimo_inicio, max(ultimo_fim, fim))
        else:
            mesclados.append((inicio, fim))

    return mesclados
