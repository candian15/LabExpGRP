"""Funil de seleção: quantos repositórios sobraram em cada etapa e por quê.

Requisito da seção 7 do enunciado; a tabela gerada aqui vai para a seção de
Metodologia do artigo. A entrada é a lista de linhas devolvidas por
``pipeline.selecao.avaliar``, cada uma com um ``motivo_descarte`` (vazio =
entrou na amostra).

A ordem das etapas é a mesma em que os filtros são aplicados na seleção, então
cada repositório é descartado em exatamente uma etapa.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

# (motivo registrado na seleção, critério da etapa, explicação do descarte)
ETAPAS = [
    ("sem_actions", "usam GitHub Actions", "total_count = 0 em /actions/workflows"),
    ("poucas_releases", "≥ {min_releases} releases publicadas na janela",
     "menos de {min_releases} releases publicadas na janela"),
    ("poucos_runs", "≥ {min_runs} workflow runs válidos na janela",
     "menos de {min_runs} runs válidos de push no default branch"),
    ("erro", "coleta concluída sem erro", "erro definitivo da API (ver log)"),
]

CAMPOS = ["etapa", "restantes", "descartados", "motivo_do_descarte"]


def linhas(
    avaliacoes: list[dict],
    min_releases: int = 5,
    min_runs: int = 50,
    n_candidatos: int | None = None,
    busca: str = "stars:>1000",
) -> list[dict]:
    """Tabela do funil, uma linha por etapa.

    ``n_candidatos`` é o total que a busca devolveu. Quando ele é maior que o
    número de repositórios avaliados, a coleta parou ao fechar a amostra, e isso
    aparece como uma etapa própria em vez de desaparecer da conta.
    """
    motivos = Counter(a.get("motivo_descarte") or "" for a in avaliacoes)
    restantes = n_candidatos if n_candidatos is not None else len(avaliacoes)
    tabela = [_linha(f"candidatos da busca ({busca})", restantes)]

    if restantes > len(avaliacoes):
        nao_avaliados = restantes - len(avaliacoes)
        restantes = len(avaliacoes)
        tabela.append(_linha("avaliados", restantes, nao_avaliados,
                             "não avaliado: a amostra já estava completa"))

    for motivo, criterio, explicacao in ETAPAS:
        descartados = motivos.get(motivo, 0)
        restantes -= descartados
        tabela.append(_linha(
            criterio.format(min_releases=min_releases, min_runs=min_runs),
            restantes,
            descartados,
            explicacao.format(min_releases=min_releases, min_runs=min_runs),
        ))

    tabela.append(_linha("amostra final", restantes))
    return tabela


def _linha(etapa: str, restantes: int, descartados: int | str = "", motivo: str = "") -> dict:
    return {
        "etapa": etapa,
        "restantes": restantes,
        "descartados": descartados,
        "motivo_do_descarte": motivo,
    }


def salvar_csv(registros: list[dict], campos: list[str], caminho: str | Path) -> None:
    """Escreve um CSV com as colunas em ``campos`` (as demais chaves são ignoradas)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(registros)


def imprimir(tabela: list[dict]) -> None:
    largura = max(len(l["etapa"]) for l in tabela)
    for l in tabela:
        descarte = f"  (-{l['descartados']}: {l['motivo_do_descarte']})" if l["descartados"] else ""
        print(f"  {l['etapa']:<{largura}}  {l['restantes']:>5}{descarte}")
