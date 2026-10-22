"""Intervalos de confiança por bootstrap para os números principais das RQ 01 a 07.

Para cada estatística, sorteamos com reposição 2.000 amostras de repositórios do
mesmo tamanho da original e recalculamos o valor em cada uma. O intervalo de 95% vai
do percentil 2,5 ao 97,5 dessas réplicas (bootstrap percentil). A semente é fixa,
então o resultado se repete.

- RQ 01 a 04: mediana de cada métrica (os vazios ficam fora, como na descritiva);
- RQ 03: ρ de Spearman entre as duas variantes do CFR;
- RQ 05: ρ de Spearman entre a frequência e cada variante do CFR;
- RQ 07: % de repositórios que mudam de categoria em cada par de combinações.

Uso (a partir de LAB03/, depois da RQ 07)::

    python -m analises.ic_bootstrap --csv dados/repositorios.csv --rq7 resultados/rq7_classificacoes.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analises.rq1_rq4_descritiva import metricas
from analises.utils import CANDIDATAS_CFR_B, COL_CFR_A, COL_FREQUENCIA, achar_coluna, carregar_repositorios

REPLICAS = 2000
SEMENTE = 42
PARES = [("C1", "C2"), ("C1", "C3"), ("C2", "C3")]


def intervalo(valores: np.ndarray) -> tuple[float, float]:
    """Percentis 2,5 e 97,5 das réplicas (ignorando réplicas sem valor)."""
    v = valores[~np.isnan(valores)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def replicas_mediana(serie: pd.Series, indices: np.ndarray) -> np.ndarray:
    """Mediana de cada réplica; os vazios da série continuam fora da conta."""
    x = serie.to_numpy(dtype=float)[indices]
    with np.errstate(all="ignore"):
        return np.nanmedian(x, axis=1)


def replicas_spearman(x: pd.Series, y: pd.Series, indices: np.ndarray) -> np.ndarray:
    a, b = x.to_numpy(dtype=float), y.to_numpy(dtype=float)
    out = np.empty(len(indices))
    for i, idx in enumerate(indices):
        xa, yb = a[idx], b[idx]
        ok = ~(np.isnan(xa) | np.isnan(yb))
        out[i] = spearmanr(xa[ok], yb[ok])[0] if ok.sum() > 2 else np.nan
    return out


def replicas_mudanca(c1: pd.Series, c2: pd.Series, indices: np.ndarray) -> np.ndarray:
    """% de repositórios com categoria diferente entre as duas combinações."""
    mudou = (c1.to_numpy() != c2.to_numpy()).astype(float)
    return 100 * mudou[indices].mean(axis=1)


def tabela(df: pd.DataFrame, rq7: pd.DataFrame | None, col_cfr_b: str,
           replicas: int = REPLICAS, semente: int = SEMENTE) -> pd.DataFrame:
    rng = np.random.default_rng(semente)
    linhas = []

    idx = rng.integers(0, len(df), size=(replicas, len(df)))
    for d in metricas(col_cfr_b):
        s = df[d["coluna"]]
        lo, hi = intervalo(replicas_mediana(s, idx))
        linhas.append({"rq": d["rq"], "estatistica": f"mediana {d['rotulo']}",
                       "valor": float(s.median()), "ic95_inf": lo, "ic95_sup": hi})

    ok = df[[COL_CFR_A, col_cfr_b]].dropna()
    lo, hi = intervalo(replicas_spearman(df[COL_CFR_A], df[col_cfr_b], idx))
    linhas.append({"rq": "RQ03", "estatistica": "rho CFR (a) x CFR (b)",
                   "valor": float(spearmanr(ok[COL_CFR_A], ok[col_cfr_b])[0]),
                   "ic95_inf": lo, "ic95_sup": hi})

    for variante, col in [("a", COL_CFR_A), ("b", col_cfr_b)]:
        ok = df[[COL_FREQUENCIA, col]].dropna()
        rho = float(spearmanr(ok[COL_FREQUENCIA], ok[col])[0])
        lo, hi = intervalo(replicas_spearman(df[COL_FREQUENCIA], df[col], idx))
        linhas.append({"rq": "RQ05", "estatistica": f"rho frequência x CFR ({variante})",
                       "valor": rho, "ic95_inf": lo, "ic95_sup": hi})

    if rq7 is not None:
        idx7 = rng.integers(0, len(rq7), size=(replicas, len(rq7)))
        for a, b in PARES:
            valor = 100 * float((rq7[a] != rq7[b]).mean())
            lo, hi = intervalo(replicas_mudanca(rq7[a], rq7[b], idx7))
            linhas.append({"rq": "RQ07", "estatistica": f"% que muda {a} x {b}",
                           "valor": valor, "ic95_inf": lo, "ic95_sup": hi})
    return pd.DataFrame(linhas)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m analises.ic_bootstrap",
                                 description=__doc__.split("\n")[0])
    ap.add_argument("--csv", default="dados/repositorios.csv")
    ap.add_argument("--rq7", default="resultados/rq7_classificacoes.csv",
                    help="saída da RQ 07 (sem ela, a RQ 07 fica de fora)")
    ap.add_argument("--saida", default="resultados")
    ap.add_argument("--col-cfr-b", default=None, help="nome da coluna do CFR (b) no CSV")
    ap.add_argument("--replicas", type=int, default=REPLICAS)
    args = ap.parse_args(argv)

    df = carregar_repositorios(args.csv)
    col_b = achar_coluna(df, CANDIDATAS_CFR_B, args.col_cfr_b)
    rq7 = pd.read_csv(args.rq7) if Path(args.rq7).exists() else None
    t = tabela(df, rq7, col_b, args.replicas)

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    t.to_csv(saida / "ic_bootstrap.csv", index=False)
    print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\n{saida / 'ic_bootstrap.csv'} escrito ({args.replicas} réplicas, semente {SEMENTE}).")


if __name__ == "__main__":
    main()
