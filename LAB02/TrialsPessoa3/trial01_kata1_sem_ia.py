"""
Kata 1 — Normalizador de agenda de horários

Dada uma lista de intervalos de horário (tuplas de inteiros representando minutos
do dia, ex.: (60, 120) = das 01:00 às 02:00), mesclar os intervalos sobrepostos
ou adjacentes e retornar a lista consolidada, ordenada pelo horário de início.

Exemplo:
    normalizar_agenda([(60, 120), (100, 150), (200, 220)])
    -> [(60, 150), (200, 220)]

Regra de adjacência: dois intervalos que se tocam exatamente (fim de um == início
do outro) também devem ser mesclados. Ex.: (60, 100) e (100, 150) viram (60, 150).
"""


def normalizar_agenda(intervalos):
    if not intervalos:
        return []

    intervalos = sorted(intervalos, key=lambda x: x[0])

    resultado = [intervalos[0]]

    for inicio, fim in intervalos[1:]:
        ultimo_inicio, ultimo_fim = resultado[-1]

        if inicio <= ultimo_fim:  # sobreposição ou adjacência
            resultado[-1] = (ultimo_inicio, max(ultimo_fim, fim))
        else:
            resultado.append((inicio, fim))

    return resultado