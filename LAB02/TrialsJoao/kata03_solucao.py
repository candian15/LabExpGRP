def calcular_troco(valor, moedas):
    """Menor numero de moedas para compor 'valor', ou -1 se impossivel.

    Ver a especificacao do kata 3 em katas.json (campo "especificacao").
    """
    infinito = float("inf")
    # dp[v] = menor numero de moedas para somar exatamente v.
    dp = [0] + [infinito] * valor

    for v in range(1, valor + 1):
        for moeda in moedas:
            if moeda <= v and dp[v - moeda] + 1 < dp[v]:
                dp[v] = dp[v - moeda] + 1

    return dp[valor] if dp[valor] != infinito else -1
