"""Change failure rate, variante (a): proxy de CI (RQ 03a).

CFR(a) = nº de runs com falha / (nº de falhas + nº de sucessos)

Classificação pelo campo ``conclusion`` (seção 3 do enunciado):
- sucesso: ``success``
- falha:   ``failure``, ``timed_out``, ``startup_failure``
- ignorar: ``cancelled``, ``skipped``, ``neutral``, ``action_required``,
  ``stale`` ou vazio (execução em andamento) — não entra em cálculo nenhum.

Atenção: isso mede falha de *pipeline*, não falha em produção.
Considera todos os workflows do repositório juntos (FAQ do enunciado).
"""

from __future__ import annotations

from typing import Iterable

SUCESSO = "sucesso"
FALHA = "falha"

CONCLUSOES_SUCESSO = frozenset({"success"})
CONCLUSOES_FALHA = frozenset({"failure", "timed_out", "startup_failure"})


def classificar_conclusion(conclusion: str | None) -> str | None:
    """Retorna "sucesso", "falha" ou None (run ignorado)."""
    if conclusion in CONCLUSOES_SUCESSO:
        return SUCESSO
    if conclusion in CONCLUSOES_FALHA:
        return FALHA
    return None


def runs_validos(runs: Iterable[dict]) -> list[dict]:
    """Só os runs que contam (sucesso ou falha). Útil para o filtro de ≥ 50 runs válidos."""
    return [r for r in runs if classificar_conclusion(r.get("conclusion")) is not None]


def contar_ci(runs: Iterable[dict]) -> tuple[int, int]:
    """(nº de falhas, nº de sucessos)."""
    falhas = sucessos = 0
    for r in runs:
        c = classificar_conclusion(r.get("conclusion"))
        if c == FALHA:
            falhas += 1
        elif c == SUCESSO:
            sucessos += 1
    return falhas, sucessos


def cfr_ci(runs: Iterable[dict]) -> float | None:
    """CFR (a) entre 0 e 1. None se não houver nenhum run válido."""
    falhas, sucessos = contar_ci(runs)
    total = falhas + sucessos
    if total == 0:
        return None
    return falhas / total
