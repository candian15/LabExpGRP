"""Comando único do pipeline: ``python -m pipeline --config config.yaml``.

Encadeia as três partes do grupo:

1. busca e seleciona os repositórios (``pipeline.selecao``);
2. coleta releases/commits (``pipeline.coleta_releases``) e workflow runs
   (``pipeline.coleta_runs``) de quem passou pelos filtros;
3. calcula as métricas DORA, classifica cada repositório e escreve os CSVs.

Saídas, na pasta indicada em ``saida`` no config:

- ``repositorios.csv``: uma linha por candidato avaliado, com metadados,
  métricas, classificação DORA e o motivo do descarte quando houver;
- ``funil.csv``: quantos repositórios sobraram em cada etapa da seleção.

O token vem da variável de ambiente ``GITHUB_TOKEN``. Cada resposta da API fica
em ``cache/``, então rodar o comando de novo continua de onde parou sem gastar
cota. ``Ctrl+C`` salva o que já foi coletado.
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime
from pathlib import Path

import yaml

from metricas.cfr import cfr_ci
from metricas.cfr_entrega import VERSAO_PADRAO, cfr_entrega
from metricas.classificacao import classificar
from metricas.frequencia import deployment_frequency
from metricas.lead_time import lead_time_repo
from metricas.recuperacao import tempo_recuperacao
from pipeline import funil
from pipeline.coleta_releases import coletar_releases
from pipeline.github_client import ErroGitHub, GitHubClient
from pipeline.selecao import CAMPOS_META, avaliar, buscar_candidatos

log = logging.getLogger(__name__)

PASSO_PROGRESSO = 25  # a cada N candidatos avaliados, uma linha de progresso no log

CAMPOS_SAIDA = CAMPOS_META + [
    "n_releases",
    "n_runs_validos",
    "deployment_frequency",
    "lead_time_a_horas",
    "lead_time_b_horas",
    "cfr_ci",
    "cfr_entrega",
    "cfrb_releases_avaliadas",
    "cfrb_releases_falha",
    "cfrb_releases_censuradas",
    "cfrb_releases_corretivas",
    "cfrb_heuristica",
    "recuperacao_horas",
    "n_episodios",
    "prop_censurados",
    "releases_404",
    "nota_frequencia",
    "nota_lead_time",
    "nota_cfr",
    "nota_recuperacao",
    "dora_nota",
    "dora",
    "motivo_descarte",
]


def _data(valor) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor))


def carregar_config(caminho: str | Path) -> dict:
    """Lê o config.yaml e aplica os padrões do enunciado."""
    cfg = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    janela = cfg.get("janela") or {}
    if not janela.get("inicio") or not janela.get("fim"):
        raise SystemExit(
            f"{caminho}: defina janela.inicio e janela.fim com as datas fixadas pelo professor."
        )
    busca = cfg.get("busca") or {}
    selecao = cfg.get("selecao") or {}
    return {
        "inicio": _data(janela["inicio"]),
        "fim": _data(janela["fim"]),
        "faixas_estrelas": busca.get("faixas_estrelas") or [">1000"],
        "linguagens": busca.get("linguagens") or [],
        "min_releases": int(selecao.get("min_releases", 5)),
        "min_runs": int(selecao.get("min_runs", 50)),
        "max_repositorios": int(selecao.get("max_repositorios", 100)),
        "contribuidores": bool(selecao.get("contribuidores", True)),
        "heuristica_cfrb": str(selecao.get("heuristica_cfrb") or VERSAO_PADRAO),
        "cache": cfg.get("cache", "cache"),
        "saida": cfg.get("saida", "dados"),
    }


def metricas_do_repo(linha: dict, comparacoes: list[dict], runs: list[dict],
                     inicio: date, fim: date, heuristica: str = VERSAO_PADRAO) -> dict:
    """Métricas DORA e classificação de um repositório selecionado (sem rede).

    Calcula as duas variantes obrigatórias de cada métrica com variante: lead
    time (a) e (b), e CFR (a), proxy de CI, e (b), proxy de entrega.

    A classificação usa a combinação de referência C1 da RQ 07: release como
    unidade de deploy, lead time na variante (a) e CFR na variante (a). As
    variantes (b) ficam no CSV para a análise de sensibilidade da RQ 07.
    """
    lead = lead_time_repo(comparacoes)
    recuperacao = tempo_recuperacao(runs)
    frequencia = deployment_frequency(linha["n_releases"], inicio, fim)
    cfr = cfr_ci(runs)
    entrega = cfr_entrega(comparacoes, fim, heuristica)
    return {
        "deployment_frequency": round(frequencia, 4),
        "lead_time_a_horas": _arredondar(lead["lead_time_a_horas"]),
        "lead_time_b_horas": _arredondar(lead["lead_time_b_horas"]),
        "releases_404": lead["releases_404"],
        "cfr_ci": _arredondar(cfr),
        "cfr_entrega": _arredondar(entrega["cfr_entrega"]),
        "cfrb_releases_avaliadas": entrega["n_avaliadas"],
        "cfrb_releases_falha": entrega["n_falhas"],
        "cfrb_releases_censuradas": entrega["n_censuradas"],
        "cfrb_releases_corretivas": entrega["n_corretivas"],
        "cfrb_heuristica": heuristica,
        "recuperacao_horas": _arredondar(recuperacao["mediana_horas"]),
        "n_episodios": recuperacao["n_episodios"],
        "prop_censurados": _arredondar(recuperacao["prop_censurados"]),
        **classificar(frequencia, lead["lead_time_a_horas"], cfr, recuperacao["mediana_horas"]),
    }


def _arredondar(valor: float | None, casas: int = 4) -> float | None:
    return None if valor is None else round(valor, casas)


def processar_repo(gh: GitHubClient, repo: dict, cfg: dict) -> dict:
    """Avalia um candidato e, se ele entrar na amostra, calcula suas métricas."""
    try:
        linha = avaliar(gh, repo, cfg["inicio"], cfg["fim"], cfg["min_releases"],
                        cfg["min_runs"], cfg["contribuidores"])
        runs = linha.pop("runs")
        if not linha["motivo_descarte"]:
            owner, nome = linha["repo"].split("/", 1)
            dados = coletar_releases(gh, owner, nome, cfg["inicio"], cfg["fim"])
            linha.update(metricas_do_repo(linha, dados["comparacoes"], runs,
                                          cfg["inicio"], cfg["fim"], cfg["heuristica_cfrb"]))
        return linha
    except ErroGitHub as e:
        log.warning("%s descartado por erro da API: %s", repo.get("full_name"), e)
        return {"repo": repo.get("full_name"), "motivo_descarte": "erro"}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="Pipeline de coleta das métricas DORA (Lab03).",
    )
    ap.add_argument("--config", default="config.yaml", help="arquivo de configuração")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = carregar_config(args.config)
    gh = GitHubClient(cache_dir=cfg["cache"])
    print(f"Janela: {cfg['inicio']} a {cfg['fim']} | alvo: {cfg['max_repositorios']} repositórios"
          f" | heurística do CFR (b): {cfg['heuristica_cfrb']}")

    candidatos = buscar_candidatos(gh, cfg["faixas_estrelas"], cfg["linguagens"])
    print(f"{len(candidatos)} candidatos na busca.\n")

    avaliacoes: list[dict] = []
    aprovados = 0
    try:
        for i, repo in enumerate(candidatos, 1):
            if aprovados >= cfg["max_repositorios"]:
                break
            linha = processar_repo(gh, repo, cfg)
            avaliacoes.append(linha)
            if not linha["motivo_descarte"]:
                aprovados += 1
                print(f"  [{aprovados:>3}/{cfg['max_repositorios']}] {linha['repo']}: "
                      f"{linha['dora']} (freq {linha['deployment_frequency']}/sem, "
                      f"CFR {linha['cfr_ci']})", flush=True)
            elif i % PASSO_PROGRESSO == 0:
                # A coleta completa leva horas; sem isso o log fica mudo por
                # minutos sempre que vários candidatos seguidos são descartados.
                print(f"  ... {i} candidatos avaliados, {aprovados} aprovados, "
                      f"{gh.chamadas_api} chamadas à API", flush=True)
    except KeyboardInterrupt:
        print("\nInterrompido. Salvando o que já foi coletado "
              "(rodar o comando de novo continua do cache).")

    pasta = Path(cfg["saida"])
    funil.salvar_csv(avaliacoes, CAMPOS_SAIDA, pasta / "repositorios.csv")
    tabela = funil.linhas(avaliacoes, cfg["min_releases"], cfg["min_runs"],
                          n_candidatos=len(candidatos),
                          busca=", ".join(f"stars:{f}" for f in cfg["faixas_estrelas"]))
    funil.salvar_csv(tabela, funil.CAMPOS, pasta / "funil.csv")

    print("\nFunil de seleção:")
    funil.imprimir(tabela)
    print(f"\n{pasta/'repositorios.csv'} e {pasta/'funil.csv'} escritos.")
    print(f"Chamadas à API: {gh.chamadas_api} | respostas do cache: {gh.acertos_cache}")


if __name__ == "__main__":
    main()
