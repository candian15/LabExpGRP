"""
Kata 6 — Escalonador de tarefas com prioridades customizadas

Dado um dicionário de dependências (tarefa -> lista de tarefas que precisam
ser executadas ANTES dela) e um dicionário de prioridades (tarefa -> número,
quanto MAIOR o número, MAIOR a prioridade), retornar uma lista com a ordem
válida de execução de todas as tarefas.

Regra de desempate: entre as tarefas que já podem ser executadas (todas as
dependências satisfeitas) em um dado momento, escolher primeiro a de MAIOR
prioridade; em caso de empate de prioridade, escolher a que vem primeiro em
ordem alfabética.

Exemplo:
    escalonar_tarefas(
        dependencias={"A": [], "B": ["A"], "C": ["A"]},
        prioridades={"A": 1, "B": 5, "C": 5},
    )
    -> ["A", "B", "C"]   # B e C empatam em prioridade, B vence por ordem alfabética
"""


import heapq


def escalonar_tarefas(dependencias, prioridades):
    concluidas = set()
    resultado = []
    disponiveis = []

    for tarefa, deps in dependencias.items():
        if not deps:
            heapq.heappush(disponiveis, (-prioridades[tarefa], tarefa))

    while disponiveis:
        _, tarefa = heapq.heappop(disponiveis)
        resultado.append(tarefa)
        concluidas.add(tarefa)

        for t, deps in dependencias.items():
            if (t not in concluidas
                    and t not in resultado
                    and set(deps).issubset(concluidas)
                    and all(x[1] != t for x in disponiveis)):
                heapq.heappush(disponiveis, (-prioridades[t], t))

    return resultado