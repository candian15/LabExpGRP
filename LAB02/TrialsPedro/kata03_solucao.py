def calcular_troco(valor, moedas):
    """Menor numero de moedas que soma exatamente 'valor', ou -1.

    Ver especificacao do kata 3 em katas.json (campo "especificacao").
    Programacao dinamica: o guloso falha com moedas arbitrarias.
    """
    if valor == 0:
        return 0

    infinito = float("inf")
    minimo = [0] + [infinito] * valor
    uteis = [m for m in moedas if 0 < m <= valor]

    for atual in range(1, valor + 1):
        for moeda in uteis:
            if moeda <= atual and minimo[atual - moeda] + 1 < minimo[atual]:
                minimo[atual] = minimo[atual - moeda] + 1

    return -1 if minimo[valor] == infinito else minimo[valor]
