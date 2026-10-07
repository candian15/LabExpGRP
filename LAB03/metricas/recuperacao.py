"""Tempo de recuperação após falha de CI (RQ 04).

Regras (seção 5 do enunciado):
- os runs são agrupados por workflow e ordenados cronologicamente;
- um episódio de falha começa na primeira falha *após um sucesso* e termina na
  próxima execução bem-sucedida do mesmo workflow;
- duração = ``updated_at`` do sucesso − ``run_started_at`` da primeira falha;
- runs ignorados (cancelled, skipped...) não abrem nem fecham episódio;
- episódio que não termina dentro da janela é **censurado**: não entra na
  mediana, mas é contado e reportado como proporção;
- valor do repositório = mediana dos episódios de todos os workflows.

Decisão do grupo (documentar no artigo): falhas que aparecem no início da
janela antes de qualquer sucesso daquele workflow não abrem episódio, porque o
enunciado define o início como "primeira falha após um sucesso" e não sabemos
quando essa falha começou de verdade. Elas são contadas em
``falhas_sem_sucesso_anterior``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Iterable

from metricas.cfr import FALHA, SUCESSO, classificar_conclusion

_SEM_DATA = datetime.min.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class Episodio:
    workflow_id: object
    inicio: datetime
    fim: datetime | None  # None = censurado

    @property
    def censurado(self) -> bool:
        return self.fim is None

    @property
    def horas(self) -> float | None:
        if self.fim is None:
            return None
        return (self.fim - self.inicio).total_seconds() / 3600


def _data(valor: str | datetime | None) -> datetime | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def _inicio_run(run: dict) -> datetime | None:
    return _data(run.get("run_started_at")) or _data(run.get("created_at"))


def episodios_do_workflow(runs: Iterable[dict]) -> tuple[list[Episodio], int]:
    """Episódios de um único workflow.

    Retorna (episódios, nº de falhas iniciais sem sucesso anterior).
    """
    ordenados = sorted(
        (r for r in runs if classificar_conclusion(r.get("conclusion")) is not None),
        key=lambda r: _inicio_run(r) or _SEM_DATA,
    )
    episodios: list[Episodio] = []
    houve_sucesso = False
    inicio_falha: datetime | None = None
    falhas_iniciais = 0
    workflow_id = None

    for run in ordenados:
        workflow_id = run.get("workflow_id", workflow_id)
        tipo = classificar_conclusion(run.get("conclusion"))
        if tipo == FALHA:
            if not houve_sucesso:
                falhas_iniciais += 1
            elif inicio_falha is None:
                inicio_falha = _inicio_run(run)
            # falha seguinte dentro de um episódio aberto: mesmo episódio
        elif tipo == SUCESSO:
            if inicio_falha is not None:
                episodios.append(Episodio(workflow_id, inicio_falha, _data(run.get("updated_at"))))
                inicio_falha = None
            houve_sucesso = True

    if inicio_falha is not None:
        episodios.append(Episodio(workflow_id, inicio_falha, None))  # censurado
    return episodios, falhas_iniciais


def episodios_do_repo(runs: Iterable[dict]) -> tuple[list[Episodio], int]:
    """Episódios de todos os workflows do repositório (calculados dentro de cada workflow)."""
    por_workflow: dict[object, list[dict]] = defaultdict(list)
    for run in runs:
        por_workflow[run.get("workflow_id")].append(run)

    todos: list[Episodio] = []
    falhas_iniciais = 0
    for runs_wf in por_workflow.values():
        eps, iniciais = episodios_do_workflow(runs_wf)
        todos.extend(eps)
        falhas_iniciais += iniciais
    return todos, falhas_iniciais


def tempo_recuperacao(runs: Iterable[dict]) -> dict:
    """Resumo da RQ 04 para um repositório.

    Chaves:
    - ``mediana_horas``: mediana dos episódios concluídos (None se não houver);
    - ``n_episodios``: total de episódios (concluídos + censurados);
    - ``n_censurados`` e ``prop_censurados``;
    - ``falhas_sem_sucesso_anterior``.
    """
    episodios, falhas_iniciais = episodios_do_repo(runs)
    duracoes = [e.horas for e in episodios if not e.censurado]
    n = len(episodios)
    n_censurados = n - len(duracoes)
    return {
        "mediana_horas": median(duracoes) if duracoes else None,
        "n_episodios": n,
        "n_censurados": n_censurados,
        "prop_censurados": (n_censurados / n) if n else None,
        "falhas_sem_sucesso_anterior": falhas_iniciais,
    }
