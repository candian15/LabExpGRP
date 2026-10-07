"""Fixtures compartilhadas: runs construídos à mão com resultado conhecido."""

import pytest


def run(hora, conclusion, workflow_id=1, fim=None, dia="2026-03-10", id_=None):
    """Monta um workflow run mínimo. ``hora`` e ``fim`` no formato HH:MM."""
    inicio = f"{dia}T{hora}:00Z"
    return {
        "id": id_ or hash((hora, conclusion, workflow_id, dia)),
        "workflow_id": workflow_id,
        "event": "push",
        "head_branch": "main",
        "conclusion": conclusion,
        "created_at": inicio,
        "run_started_at": inicio,
        "updated_at": f"{dia}T{fim or hora}:00Z",
    }


@pytest.fixture
def exemplo_enunciado():
    """Tabela da RQ 04: falha às 10:00, recupera às 11:15 (termina 11:20) -> 1h20."""
    return [
        run("09:00", "success", fim="09:05"),
        run("10:00", "failure", fim="10:05"),
        run("10:30", "failure", fim="10:35"),
        run("11:15", "success", fim="11:20"),
    ]
