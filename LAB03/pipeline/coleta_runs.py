"""Coleta dos workflow runs do default branch dentro da janela de observação.

Regras do enunciado (seções 3 e 4):
- só runs do default branch disparados por ``push`` (``event=push``);
- só runs criados dentro da janela;
- a busca com filtros devolve no máximo 1.000 resultados por consulta, então a
  janela é dividida por mês; se algum mês ainda passar de 1.000, ele é dividido
  ao meio (recursivamente) até caber.

Rodar sozinho, para testar com um repositório::

    export GITHUB_TOKEN=ghp_...
    python -m pipeline.coleta_runs psf/requests --inicio 2025-09-01 --fim 2026-08-31
"""

from __future__ import annotations

import argparse
import calendar
import csv
import logging
from datetime import date, timedelta
from pathlib import Path

from pipeline.github_client import GitHubClient

log = logging.getLogger(__name__)

TETO_BUSCA = 1000

CAMPOS_RUN = [
    "id",
    "workflow_id",
    "name",
    "event",
    "head_branch",
    "head_sha",
    "status",
    "conclusion",
    "run_attempt",
    "created_at",
    "run_started_at",
    "updated_at",
]


def meses_da_janela(inicio: date, fim: date) -> list[tuple[date, date]]:
    """Divide [inicio, fim] (inclusivo) em fatias por mês do calendário."""
    if fim < inicio:
        raise ValueError("fim da janela antes do início")
    fatias = []
    atual = inicio
    while atual <= fim:
        ultimo_dia = calendar.monthrange(atual.year, atual.month)[1]
        fim_mes = min(date(atual.year, atual.month, ultimo_dia), fim)
        fatias.append((atual, fim_mes))
        atual = fim_mes + timedelta(days=1)
    return fatias


def _dividir_ao_meio(a: date, b: date) -> list[tuple[date, date]]:
    meio = a + (b - a) // 2
    return [(a, meio), (meio + timedelta(days=1), b)]


def _resumir_run(run: dict) -> dict:
    return {campo: run.get(campo) for campo in CAMPOS_RUN}


def coletar_runs_periodo(gh: GitHubClient, owner: str, repo: str, branch: str, a: date, b: date) -> list[dict]:
    """Runs de push no branch entre as datas a e b (inclusivo), respeitando o teto de 1.000."""
    caminho = f"/repos/{owner}/{repo}/actions/runs"
    params = {
        "branch": branch,
        "event": "push",
        "created": f"{a.isoformat()}..{b.isoformat()}",
        "per_page": 100,
    }
    primeira = gh.get(caminho, params)
    total = primeira.get("total_count", 0)

    if total > TETO_BUSCA:
        if a < b:
            log.info("%s/%s: %d runs em %s..%s (> %d); dividindo o período", owner, repo, total, a, b, TETO_BUSCA)
            runs = []
            for x, y in _dividir_ao_meio(a, b):
                runs.extend(coletar_runs_periodo(gh, owner, repo, branch, x, y))
            return runs
        log.warning(
            "%s/%s: %d runs só no dia %s; a API devolve no máximo %d (registrar como ameaça à validade)",
            owner, repo, total, a, TETO_BUSCA,
        )

    return [_resumir_run(r) for r in gh.listar(caminho, params)]


def coletar_runs(gh: GitHubClient, owner: str, repo: str, branch: str, inicio: date, fim: date) -> list[dict]:
    """Todos os runs de push no default branch dentro da janela, sem duplicatas, em ordem cronológica."""
    por_id: dict[int, dict] = {}
    for a, b in meses_da_janela(inicio, fim):
        for run in coletar_runs_periodo(gh, owner, repo, branch, a, b):
            # Filtro defensivo: a API às vezes ignora filtros em casos raros.
            if run.get("event") != "push" or run.get("head_branch") != branch:
                continue
            por_id[run["id"]] = run
    return sorted(por_id.values(), key=lambda r: (r.get("run_started_at") or r.get("created_at") or ""))


def repo_usa_actions(gh: GitHubClient, owner: str, repo: str) -> bool:
    """``total_count = 0`` em /actions/workflows: o repositório não usa Actions."""
    dados = gh.get(f"/repos/{owner}/{repo}/actions/workflows", {"per_page": 1})
    return dados.get("total_count", 0) > 0


def salvar_runs_csv(runs: list[dict], caminho: str | Path, repo_completo: str | None = None) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = (["repo"] if repo_completo else []) + CAMPOS_RUN
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for run in runs:
            linha = dict(run)
            if repo_completo:
                linha["repo"] = repo_completo
            w.writerow({c: linha.get(c) for c in campos})


def _main() -> None:
    from metricas.cfr import contar_ci, cfr_ci
    from metricas.recuperacao import tempo_recuperacao

    ap = argparse.ArgumentParser(description="Coleta os workflow runs de um repositório na janela.")
    ap.add_argument("repo", help="owner/nome, ex.: psf/requests")
    ap.add_argument("--inicio", required=True, type=date.fromisoformat)
    ap.add_argument("--fim", required=True, type=date.fromisoformat)
    ap.add_argument("--saida", default=None, help="CSV de saída (padrão: dados/runs/<owner>__<repo>.csv)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    owner, nome = args.repo.split("/", 1)
    gh = GitHubClient()
    if not repo_usa_actions(gh, owner, nome):
        print(f"{args.repo} não usa GitHub Actions.")
        return
    branch = gh.get(f"/repos/{owner}/{nome}")["default_branch"]
    runs = coletar_runs(gh, owner, nome, branch, args.inicio, args.fim)

    saida = args.saida or f"dados/runs/{owner}__{nome}.csv"
    salvar_runs_csv(runs, saida, args.repo)

    falhas, sucessos = contar_ci(runs)
    rec = tempo_recuperacao(runs)
    print(f"{args.repo} (branch {branch}): {len(runs)} runs coletados -> {saida}")
    print(f"  válidos: {falhas + sucessos} (falhas {falhas}, sucessos {sucessos})")
    print(f"  CFR (a): {cfr_ci(runs)}")
    print(f"  recuperação: {rec}")
    print(f"  chamadas à API: {gh.chamadas_api} | do cache: {gh.acertos_cache}")


if __name__ == "__main__":
    _main()
