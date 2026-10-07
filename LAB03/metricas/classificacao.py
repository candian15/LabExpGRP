"""Classificação DORA de um repositório (tabela de referência da seção 5).

Cada métrica recebe uma nota: 4 = Elite, 3 = High, 2 = Medium, 1 = Low. A
categoria geral do repositório é a **mediana** das quatro notas, arredondada
para baixo. Exemplo do enunciado: notas (4, 3, 3, 1) -> mediana 3 -> High.

Cortes fixos da disciplina:

| Métrica              | Elite    | High            | Medium           | Low      |
|----------------------|----------|-----------------|------------------|----------|
| Deployment frequency | ≥ 7/sem  | ≥ 1 e < 7/sem   | ≥ 1/mês e < 1/sem| < 1/mês  |
| Lead time (mediana)  | < 1 dia  | 1 dia a < 1 sem | 1 sem a < 30 dias| ≥ 30 dias|
| Change failure rate  | ≤ 15%    | > 15% e ≤ 30%   | > 30% e ≤ 45%    | > 45%    |
| Recuperação (mediana)| < 1 h    | 1 h a < 1 dia   | 1 dia a < 1 sem  | ≥ 1 sem  |

Unidades esperadas (as mesmas que os outros módulos devolvem):
- ``deployment_frequency``: releases por semana (``metricas.frequencia``);
- ``lead_time_horas``: mediana em horas (``metricas.lead_time``);
- ``cfr``: fração de 0 a 1 (``metricas.cfr``);
- ``recuperacao_horas``: mediana em horas (``metricas.recuperacao``).

Métrica indisponível (``None``) não recebe nota e fica fora da mediana; se
nenhuma estiver disponível, a categoria geral também é ``None``. Isso mantém a
classificação possível para repositórios em que, por exemplo, nenhuma release
teve commits comparáveis.
"""

from __future__ import annotations

from math import floor
from statistics import median
from typing import Iterable

ELITE, HIGH, MEDIUM, LOW = 4, 3, 2, 1
NOMES = {ELITE: "Elite", HIGH: "High", MEDIUM: "Medium", LOW: "Low"}

HORAS_DIA = 24
HORAS_SEMANA = 7 * HORAS_DIA
HORAS_30_DIAS = 30 * HORAS_DIA
# "1 por mês" convertido para a unidade da métrica (releases por semana).
# Um mês médio tem 365,25/12 dias, então 12 releases num ano caem em Medium, e
# não em Low por arredondamento do número de semanas da janela.
DIAS_POR_MES = 365.25 / 12
POR_SEMANA_MENSAL = 7 / DIAS_POR_MES  # ≈ 0,23 release por semana


def nota_frequencia(por_semana: float | None) -> int | None:
    """Deployment frequency: aqui MAIOR é melhor."""
    if por_semana is None:
        return None
    if por_semana >= 7:
        return ELITE
    if por_semana >= 1:
        return HIGH
    if por_semana >= POR_SEMANA_MENSAL:
        return MEDIUM
    return LOW


def _nota_menor_melhor(valor: float | None, cortes: tuple, inclusivo: bool = False) -> int | None:
    """Nota das métricas em que MENOR é melhor.

    ``cortes`` vai do melhor para o pior desempenho. ``inclusivo`` usa ``<=`` em
    vez de ``<`` porque o enunciado define as faixas do CFR com ``≤`` e as dos
    tempos com ``<``.
    """
    if valor is None:
        return None
    for nota, corte in zip((ELITE, HIGH, MEDIUM), cortes):
        if (valor <= corte) if inclusivo else (valor < corte):
            return nota
    return LOW


def nota_lead_time(horas: float | None) -> int | None:
    return _nota_menor_melhor(horas, (HORAS_DIA, HORAS_SEMANA, HORAS_30_DIAS))


def nota_cfr(fracao: float | None) -> int | None:
    return _nota_menor_melhor(fracao, (0.15, 0.30, 0.45), inclusivo=True)


def nota_recuperacao(horas: float | None) -> int | None:
    return _nota_menor_melhor(horas, (1, HORAS_DIA, HORAS_SEMANA))


def categoria_geral(notas: Iterable[int | None]) -> int | None:
    """Mediana das notas disponíveis, arredondada para baixo."""
    validas = [n for n in notas if n is not None]
    if not validas:
        return None
    return floor(median(validas))


def classificar(
    deployment_frequency: float | None = None,
    lead_time_horas: float | None = None,
    cfr: float | None = None,
    recuperacao_horas: float | None = None,
) -> dict:
    """Nota de cada métrica, nota geral e nome da categoria DORA."""
    notas = {
        "nota_frequencia": nota_frequencia(deployment_frequency),
        "nota_lead_time": nota_lead_time(lead_time_horas),
        "nota_cfr": nota_cfr(cfr),
        "nota_recuperacao": nota_recuperacao(recuperacao_horas),
    }
    geral = categoria_geral(notas.values())
    return {**notas, "dora_nota": geral, "dora": NOMES.get(geral)}
