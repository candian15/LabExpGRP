"""Replicação cruzada: compara o CSV do grupo autor com o que a replicação reproduziu.

Seção 9 do enunciado, passo 2: diferença relativa por métrica e % de repositórios
com a mesma classificação DORA. O script também redige o texto das Issues de
divergência (comando, valores esperados e obtidos) para colar no repositório do
grupo autor, em ``issues_divergencia.md``.

Entradas: o CSV original do outro grupo (``--original``) e o CSV que a execução
do pipeline deles gerou sobre os 30 repositórios (``--replica``). Os repositórios
são pareados pela coluna ``--col-repo``. Sem ``--metricas``, compara todas as
colunas numéricas presentes nos dois arquivos (menos os metadados do repositório,
que mudam com o tempo).

Uso (a partir de LAB03/):

    python -m analises.comparar_replicacao --original outro_grupo.csv --replica replica_30.csv \\
        --col-dora dora --comando "python -m pipeline --config config.yaml"
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

TOLERANCIA = 0.10  # diferença relativa aceita como "pequena" (dados mudam entre coletas)
METADADOS = {"estrelas", "contribuidores", "idade_anos", "stars", "age", "contributors"}


def diferenca_relativa(original: float, replica: float) -> float:
    """|replica - original| / |original|; 0 se os dois são 0; inf se só o original é 0."""
    if pd.isna(original) or pd.isna(replica):
        return float("nan")
    if original == 0:
        return 0.0 if replica == 0 else float("inf")
    return abs(replica - original) / abs(original)


def metricas_comuns(orig: pd.DataFrame, rep: pd.DataFrame, col_repo: str, col_dora: str | None) -> list[str]:
    """Colunas numéricas presentes nos dois CSVs, sem repo, DORA nem metadados."""
    comuns = [c for c in orig.columns if c in rep.columns and c not in (col_repo, col_dora)]
    return [
        c for c in comuns
        if c.lower() not in METADADOS
        and pd.api.types.is_numeric_dtype(orig[c]) and pd.api.types.is_numeric_dtype(rep[c])
    ]


def comparar(orig: pd.DataFrame, rep: pd.DataFrame, col_repo: str, metricas: list[str]) -> pd.DataFrame:
    """Uma linha por (repositório, métrica) dos repositórios presentes nos dois CSVs."""
    junto = orig.merge(rep, on=col_repo, suffixes=("_orig", "_rep"))
    linhas = []
    for _, r in junto.iterrows():
        for m in metricas:
            o, p = r[f"{m}_orig"], r[f"{m}_rep"]
            linhas.append({
                "repo": r[col_repo], "metrica": m, "original": o, "replica": p,
                "dif_absoluta": abs(p - o) if pd.notna(o) and pd.notna(p) else float("nan"),
                "dif_relativa": diferenca_relativa(o, p),
                "so_um_lado_tem_valor": bool(pd.isna(o) != pd.isna(p)),
            })
    return pd.DataFrame(linhas, columns=["repo", "metrica", "original", "replica", "dif_absoluta",
                                          "dif_relativa", "so_um_lado_tem_valor"])


def resumo_por_metrica(longo: pd.DataFrame, tolerancia: float = TOLERANCIA) -> pd.DataFrame:
    linhas = []
    for m, g in longo.groupby("metrica", sort=False):
        rel = g["dif_relativa"].replace([np.inf], np.nan)
        validos = g["dif_relativa"].dropna()
        linhas.append({
            "metrica": m,
            "n_comparados": len(validos),
            "mediana_dif_relativa": float(rel.median()) if rel.notna().any() else float("nan"),
            "max_dif_relativa": float(validos.max()) if len(validos) else float("nan"),
            "pct_dentro_da_tolerancia": float((validos <= tolerancia).mean() * 100) if len(validos) else float("nan"),
            "n_so_um_lado_tem_valor": int(g["so_um_lado_tem_valor"].sum()),
        })
    return pd.DataFrame(linhas)


def concordancia_dora(orig: pd.DataFrame, rep: pd.DataFrame, col_repo: str, col_dora: str) -> dict:
    """% de repositórios com a mesma classificação DORA nos dois arquivos."""
    j = orig[[col_repo, col_dora]].merge(rep[[col_repo, col_dora]], on=col_repo, suffixes=("_orig", "_rep"))
    j = j.dropna()
    iguais = j[f"{col_dora}_orig"].astype(str).str.lower() == j[f"{col_dora}_rep"].astype(str).str.lower()
    return {
        "n": len(j),
        "pct_mesma_classificacao": float(iguais.mean() * 100) if len(j) else float("nan"),
        "divergentes": j[~iguais].rename(columns={f"{col_dora}_orig": "dora_original", f"{col_dora}_rep": "dora_replica"}),
    }


def redigir_issues(
    resumo: pd.DataFrame,
    longo: pd.DataFrame,
    dora: dict | None,
    ausentes_na_replica: list[str],
    tolerancia: float = TOLERANCIA,
    comando: str = "<comando executado seguindo o README>",
    max_exemplos: int = 5,
) -> str:
    """Texto das Issues de divergência, uma por problema, no formato exigido (seção 9)."""
    blocos: list[str] = []
    if ausentes_na_replica:
        lista = "\n".join(f"- `{r}`" for r in ausentes_na_replica[:15])
        blocos.append(
            "## Issue: repositórios do CSV original que a replicação não reproduziu\n\n"
            f"**Comando executado:** `{comando}`\n\n"
            f"**Esperado:** {len(ausentes_na_replica)} repositórios do subconjunto de 30 deveriam aparecer no CSV gerado.\n"
            f"**Obtido:** não aparecem no resultado da replicação:\n\n{lista}\n\n"
            "**Evidência:** `<colar a mensagem de erro ou o trecho do log>`\n"
        )
    for _, r in resumo.iterrows():
        if not (r["mediana_dif_relativa"] > tolerancia):
            continue
        g = longo[(longo["metrica"] == r["metrica"]) & longo["dif_relativa"].notna()]
        piores = g.sort_values("dif_relativa", ascending=False).head(max_exemplos)
        tabela = "\n".join(
            f"| {x.repo} | {x.original:.4g} | {x.replica:.4g} | {x.dif_relativa:.1%} |" for x in piores.itertuples()
        )
        blocos.append(
            f"## Issue: divergência em `{r['metrica']}`\n\n"
            f"**Comando executado:** `{comando}`\n\n"
            f"**Resumo:** mediana da diferença relativa = {r['mediana_dif_relativa']:.1%} "
            f"(tolerância {tolerancia:.0%}); {r['pct_dentro_da_tolerancia']:.0f}% dos {int(r['n_comparados'])} "
            "repositórios comparados ficaram dentro da tolerância.\n\n"
            "| Repositório | Esperado (CSV original) | Obtido (replicação) | Diferença relativa |\n|---|---|---|---|\n"
            f"{tabela}\n\n"
            "**Possível causa:** os repositórios continuam recebendo commits e a data de coleta é diferente; "
            "se a diferença for maior que isso explica, pode haver diferença na definição da métrica. "
            "Pedimos que confirmem como a coluna é calculada.\n"
        )
    if dora and dora["n"] and dora["pct_mesma_classificacao"] < 100:
        div = dora["divergentes"].head(15)
        tabela = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in div.itertuples(index=False, name=None))
        blocos.append(
            "## Issue: classificação DORA diferente na replicação\n\n"
            f"**Comando executado:** `{comando}`\n\n"
            f"**Resumo:** {dora['pct_mesma_classificacao']:.0f}% dos {dora['n']} repositórios mantiveram a "
            "mesma classificação.\n\n"
            "| Repositório | DORA original | DORA replicação |\n|---|---|---|\n"
            f"{tabela}\n"
        )
    if not blocos:
        return "Nenhuma divergência acima da tolerância: não há Issues de divergência a abrir.\n"
    return "# Issues de divergência (copiar cada uma para o repositório do grupo autor)\n\n" + "\n---\n\n".join(blocos)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m analises.comparar_replicacao", description=__doc__.split("\n")[0])
    ap.add_argument("--original", required=True, help="CSV do grupo autor")
    ap.add_argument("--replica", required=True, help="CSV gerado pela execução da replicação")
    ap.add_argument("--col-repo", default="repo")
    ap.add_argument("--col-dora", default="dora", help="coluna com a classificação DORA (vazio para ignorar)")
    ap.add_argument("--metricas", default=None, help="colunas a comparar, separadas por vírgula")
    ap.add_argument("--tolerancia", type=float, default=TOLERANCIA)
    ap.add_argument("--amostra", default=None, help="arquivo com os 30 repositórios escolhidos (um por linha)")
    ap.add_argument("--comando", default="<comando executado seguindo o README>")
    ap.add_argument("--saida", default="analises/saida")
    args = ap.parse_args(argv)

    orig, rep = pd.read_csv(args.original), pd.read_csv(args.replica)
    col_dora = args.col_dora if args.col_dora in orig.columns and args.col_dora in rep.columns else None
    metricas = args.metricas.split(",") if args.metricas else metricas_comuns(orig, rep, args.col_repo, col_dora)
    if not metricas:
        raise SystemExit("nenhuma coluna numérica em comum; informe --metricas")

    longo = comparar(orig, rep, args.col_repo, metricas)
    resumo = resumo_por_metrica(longo, args.tolerancia)
    dora = concordancia_dora(orig, rep, args.col_repo, col_dora) if col_dora else None
    ausentes = []
    if args.amostra:  # repositórios que deveriam ter sido reproduzidos e não vieram
        amostra = [l.strip() for l in Path(args.amostra).read_text(encoding="utf-8").splitlines() if l.strip()]
        ausentes = sorted(set(amostra) - set(rep[args.col_repo]))
    sem_original = sorted(set(rep[args.col_repo]) - set(orig[args.col_repo]))

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    longo.to_csv(saida / "replicacao_comparacao.csv", index=False)
    resumo.to_csv(saida / "replicacao_resumo.csv", index=False)
    (saida / "issues_divergencia.md").write_text(
        redigir_issues(resumo, longo, dora, ausentes, args.tolerancia, args.comando), encoding="utf-8")

    print(resumo.to_string(index=False))
    if dora:
        print(f"\nMesma classificação DORA: {dora['pct_mesma_classificacao']:.0f}% de {dora['n']} repositórios")
    if sem_original:
        print(f"\nAtenção: {len(sem_original)} repositórios da replicação não estão no CSV original e ficaram de fora.")
    print(f"\nEscrito em {saida}/ (replicacao_comparacao.csv, replicacao_resumo.csv, issues_divergencia.md)")


if __name__ == "__main__":
    main()
