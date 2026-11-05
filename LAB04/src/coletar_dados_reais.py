"""Coleta os dados reais do cenário (item b do enunciado): tempo até o merge de PRs com e sem bot de revisão.

Fonte: API de busca do GitHub (``/search/issues``), sem token, no repositório
``ant-design/ant-design``. Para cada PR mesclado na janela de observação, o tempo até o
merge é ``merged_at - created_at`` (em horas).

- grupo ``com_bot``: PRs em que o bot de revisão ``copilot-pull-request-reviewer`` (revisão automática do GitHub Copilot) comentou
  (qualificador ``commenter:app/copilot-pull-request-reviewer``);
- grupo ``sem_bot``: PRs mesclados na mesma janela em que ele **não** comentou.

PRs abertos por contas de bot (dependabot etc.) ficam de fora. De cada grupo sorteia-se
uma amostra de 30 PRs com semente fixa (``numpy.random.default_rng(42)``).

Uso (a partir de LAB04/):  python -m src.coletar_dados_reais
Gera ``data/dados_reais.csv`` e ``data/pool_completo.csv`` (todos os PRs elegíveis).
"""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = "ant-design/ant-design"
BOT = "copilot-pull-request-reviewer"
JANELA = "2026-07-01..2026-10-31"
N_POR_GRUPO = 30
SEMENTE = 42
DADOS = Path("data")
API = "https://api.github.com/search/issues"


def _get(url: str) -> dict:
    for tentativa in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lab04-teste-de-hipotese"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:  # limite de 10 buscas/minuto sem token: espera e tenta de novo
            time.sleep(15 * (tentativa + 1))
    raise RuntimeError(f"falha ao consultar {url}")


def buscar(consulta: str) -> list[dict]:
    """Todos os resultados da busca (até 1.000, o teto da API), 100 por página."""
    itens, pagina = [], 1
    while True:
        qs = urllib.parse.urlencode({"q": consulta, "per_page": 100, "page": pagina, "sort": "created", "order": "asc"})
        dados = _get(f"{API}?{qs}")
        itens += dados.get("items", [])
        if len(dados.get("items", [])) < 100 or len(itens) >= dados.get("total_count", 0):
            return itens
        pagina += 1
        time.sleep(7)


def horas_ate_merge(item: dict) -> float | None:
    merged = (item.get("pull_request") or {}).get("merged_at")
    if not merged:
        return None
    t = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return (t(merged) - t(item["created_at"])).total_seconds() / 3600


def elegiveis(itens: list[dict], grupo: str) -> list[dict]:
    out = []
    for i in itens:
        h = horas_ate_merge(i)
        if h is None or h < 0 or (i.get("user") or {}).get("type") == "Bot":
            continue
        out.append({"grupo": grupo, "pr": i["number"], "autor": i["user"]["login"], "criado_em": i["created_at"],
                    "mesclado_em": i["pull_request"]["merged_at"], "horas_ate_merge": round(h, 4), "url": i["html_url"]})
    return out


def amostrar(pool: list[dict], n: int, rng: np.random.Generator) -> list[dict]:
    if len(pool) <= n:
        return pool
    idx = rng.choice(len(pool), size=n, replace=False)
    return [pool[i] for i in sorted(idx)]


def main() -> None:
    base = f"repo:{REPO} is:pr is:merged created:{JANELA}"
    com = elegiveis(buscar(f"{base} commenter:app/{BOT}"), "com_bot")
    time.sleep(7)
    sem = elegiveis(buscar(f"{base} -commenter:app/{BOT}"), "sem_bot")
    print(f"elegíveis: com_bot={len(com)} sem_bot={len(sem)}")
    rng = np.random.default_rng(SEMENTE)
    amostra = amostrar(com, N_POR_GRUPO, rng) + amostrar(sem, N_POR_GRUPO, rng)

    DADOS.mkdir(exist_ok=True)
    campos = ["grupo", "pr", "autor", "criado_em", "mesclado_em", "horas_ate_merge", "url"]
    for nome, linhas in (("pool_completo.csv", com + sem), ("dados_reais.csv", amostra)):
        with open(DADOS / nome, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(linhas)
    print(f"gravado {len(amostra)} PRs em data/dados_reais.csv")


if __name__ == "__main__":
    main()
