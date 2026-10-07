"""Deployment frequency (RQ 01): releases publicadas por semana.

Definição operacional do enunciado (seção 5): o valor do repositório é o número
de releases publicadas na janela dividido pelo número de semanas da janela
(uma janela de 12 meses tem ≈ 52,1 semanas).

A janela é inclusiva nas duas pontas, como no resto do pipeline: a contagem de
dias é ``fim - inicio + 1``.
"""

from __future__ import annotations

from datetime import date

DIAS_POR_SEMANA = 7


def semanas_da_janela(inicio: date, fim: date) -> float:
    """Número de semanas de uma janela inclusiva."""
    dias = (fim - inicio).days + 1
    if dias <= 0:
        raise ValueError("fim da janela antes do início")
    return dias / DIAS_POR_SEMANA


def deployment_frequency(n_releases: int, inicio: date, fim: date) -> float:
    """Releases por semana. ``n_releases`` já deve estar filtrado pela janela."""
    return n_releases / semanas_da_janela(inicio, fim)
