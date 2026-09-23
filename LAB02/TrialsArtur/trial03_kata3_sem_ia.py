"""
Kata 3 — Calculadora de troco com moedas customizadas

Dado um valor inteiro e uma lista de moedas customizadas (não moedas reais
padrão; quantidade ilimitada de cada), calcular o MENOR número de moedas
necessário para somar exatamente o valor, ou retornar -1 se for impossível.

Exemplo:
    calcular_troco(15, [3, 7, 10]) -> 2   (7 + 8? não. 3+3+3+3+3=5 moedas; melhor: 3+... )
    Na verdade: 15 = 7 + 3 + 3 + ... vamos conferir nos testes.
    calcular_troco(6, [3, 7, 10])  -> 2   (3 + 3)
    calcular_troco(1, [3, 7, 10])  -> -1  (impossível)
"""


def calcular_troco(valor, moedas):
    if valor == 0:
        return 0

    infinito = float("inf")
    dp = [infinito] * (valor + 1)
    dp[0] = 0

    for v in range(1, valor + 1):
        for moeda in moedas:
            if moeda <= v:
                dp[v] = min(dp[v], dp[v - moeda] + 1)

    return -1 if dp[valor] == infinito else dp[valor]