"""Avalia a heurística de release corretiva contra o consenso da amostra-ouro.

Seção 6 do enunciado, passo 5: precisão, recall e F1 da heurística frente ao
rótulo de consenso. Se o F1 ficar abaixo de 0,70, refina-se a heurística
(``metricas/cfr_entrega.py``) e roda-se de novo; cada versão testada e o seu F1
vão para ``validacao/historico_heuristica.md`` (e para o artigo).

Entrada: ``validacao/consenso.csv``, com uma linha por release rotulada e as
colunas ``repo``, ``tag`` e ``corretiva`` (``sim``/``não``). Os nomes das
colunas podem ser trocados com ``--col-repo``, ``--col-tag`` e ``--col-rotulo``.

Uso (token em ``GITHUB_TOKEN``; as respostas da API vêm do cache da coleta):

    python -m validacao.avaliar_heuristica
    python -m validacao.avaliar_heuristica --registrar --nota "v1: patch OU fix"

Sem ``--versao`` avalia todas as versões de ``HEURISTICAS``.
"""

from __future__ import annotations

import argparse
import csv
import logging
from datetime import date
from pathlib import Path

from sklearn.metrics import precision_recall_fscore_support

from metricas.cfr_entrega import HEURISTICAS, classificar_releases

log = logging.getLogger(__name__)

LIMIAR_F1 = 0.70
SIM = {"sim", "s", "1", "true", "yes", "y"}
NAO = {"nao", "não", "n", "0", "false", "no"}


def _rotulo(valor: str) -> bool:
    v = valor.strip().lower()
    if v in SIM:
        return True
    if v in NAO:
        return False
    raise ValueError(f"rótulo inesperado em 'corretiva': {valor!r} (use sim/não)")


def carregar_consenso(
    caminho: str | Path,
    col_repo: str = "repo",
    col_tag: str = "tag",
    col_rotulo: str = "corretiva",
) -> dict[tuple[str, str], bool]:
    """Lê o consenso: (repo, tag) -> a release é corretiva?"""
    consenso: dict[tuple[str, str], bool] = {}
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f):
            consenso[(linha[col_repo].strip(), linha[col_tag].strip())] = _rotulo(linha[col_rotulo])
    return consenso


def prever(comparacoes_por_repo: dict[str, list[dict]], versao: str) -> dict[tuple[str, str], bool]:
    """Predição da heurística: (repo, tag) -> é corretiva? (sem rede)"""
    previsto: dict[tuple[str, str], bool] = {}
    for repo, comparacoes in comparacoes_por_repo.items():
        for r in classificar_releases(comparacoes, versao):
            previsto[(repo, r["tag_name"])] = r["corretiva"]
    return previsto


def avaliar(consenso: dict[tuple[str, str], bool], previsto: dict[tuple[str, str], bool]) -> dict:
    """Precisão, recall e F1 da classe "corretiva".

    Releases do consenso que a coleta não achou na janela (``sem_predicao``) ficam
    fora do cálculo e são contadas à parte.
    """
    chaves = [k for k in consenso if k in previsto]
    y_true = [consenso[k] for k in chaves]
    y_pred = [previsto[k] for k in chaves]
    vp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    vn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
    if chaves:
        precisao, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", pos_label=True, zero_division=0
        )
    else:
        precisao = recall = f1 = 0.0
    return {
        "n": len(chaves),
        "sem_predicao": len(consenso) - len(chaves),
        "vp": vp,
        "fp": fp,
        "fn": fn,
        "vn": vn,
        "precisao": float(precisao),
        "recall": float(recall),
        "f1": float(f1),
        "atinge_limiar": bool(f1 >= LIMIAR_F1),
    }


def tabela_markdown(resultados: dict[str, dict]) -> str:
    linhas = [
        "| Versão | n | VP | FP | FN | VN | Precisão | Recall | F1 | F1 ≥ 0,70 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for versao, r in resultados.items():
        linhas.append(
            f"| {versao} | {r['n']} | {r['vp']} | {r['fp']} | {r['fn']} | {r['vn']} | "
            f"{r['precisao']:.2f} | {r['recall']:.2f} | {r['f1']:.2f} | {'sim' if r['atinge_limiar'] else 'não'} |"
        )
    return "\n".join(linhas)


def registrar(resultados: dict[str, dict], caminho: str | Path, nota: str = "", hoje: date | None = None) -> None:
    """Acrescenta a tabela desta rodada ao histórico das versões testadas."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    bloco = f"\n### Rodada de {(hoje or date.today()).isoformat()}\n\n"
    if nota:
        bloco += f"{nota}\n\n"
    bloco += tabela_markdown(resultados) + "\n"
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(bloco)


def coletar_comparacoes(gh, repos: list[str], inicio: date, fim: date) -> dict[str, list[dict]]:
    """Releases e commits de cada repositório da amostra-ouro (vêm do cache da coleta)."""
    from pipeline.coleta_releases import coletar_releases

    out = {}
    for repo in repos:
        owner, nome = repo.split("/", 1)
        out[repo] = coletar_releases(gh, owner, nome, inicio, fim)["comparacoes"]
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m validacao.avaliar_heuristica", description=__doc__.split("\n")[0])
    ap.add_argument("--consenso", default="validacao/consenso.csv")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--versao", choices=sorted(HEURISTICAS), help="avalia só uma versão (padrão: todas)")
    ap.add_argument("--col-repo", default="repo")
    ap.add_argument("--col-tag", default="tag")
    ap.add_argument("--col-rotulo", default="corretiva")
    ap.add_argument("--registrar", action="store_true", help="acrescenta a tabela a validacao/historico_heuristica.md")
    ap.add_argument("--historico", default="validacao/historico_heuristica.md")
    ap.add_argument("--nota", default="", help="descrição da rodada, gravada no histórico")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from pipeline.__main__ import carregar_config
    from pipeline.github_client import GitHubClient

    cfg = carregar_config(args.config)
    consenso = carregar_consenso(args.consenso, args.col_repo, args.col_tag, args.col_rotulo)
    repos = sorted({repo for repo, _ in consenso})
    print(f"{len(consenso)} releases rotuladas em {len(repos)} repositórios.")

    gh = GitHubClient(cache_dir=cfg["cache"])
    comparacoes = coletar_comparacoes(gh, repos, cfg["inicio"], cfg["fim"])

    versoes = [args.versao] if args.versao else sorted(HEURISTICAS)
    resultados = {v: avaliar(consenso, prever(comparacoes, v)) for v in versoes}

    print("\n" + tabela_markdown(resultados))
    sem = next(iter(resultados.values()))["sem_predicao"]
    if sem:
        print(f"\nAtenção: {sem} releases do consenso não foram encontradas na janela e ficaram de fora.")
    melhor = max(resultados, key=lambda v: resultados[v]["f1"])
    if resultados[melhor]["atinge_limiar"]:
        print(f"\nMelhor versão: {melhor} (F1 = {resultados[melhor]['f1']:.2f}). Use-a como VERSAO_PADRAO.")
    else:
        print(f"\nNenhuma versão chegou a F1 ≥ {LIMIAR_F1:.2f} (melhor: {melhor}, {resultados[melhor]['f1']:.2f}). "
              "Refine a heurística em metricas/cfr_entrega.py e rode de novo.")
    if args.registrar:
        registrar(resultados, args.historico, args.nota)
        print(f"Tabela registrada em {args.historico}.")


if __name__ == "__main__":
    main()
