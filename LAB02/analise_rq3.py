#!/usr/bin/env python3
"""
analise_rq3.py - Analise da RQ3 (estrutura do codigo) - Lab02

RQ3: O uso de assistente de IA altera a complexidade ciclomatica ou a
duplicacao do codigo produzido?

O que este script faz:
  1. Le metrics.csv (complexidade, MI, LOC, duplicacao por trial).
  2. Compara os tratamentos 'ia' vs 'manual' usando MEDIANA e IQR
     (robusto ao N pequeno, como o enunciado pede).
  3. Normaliza complexidade e duplicacao por LOC (obrigatorio no enunciado:
     codigo de IA pode ser mais verboso, e olhar a metrica crua engana).
  4. Aplica o teste de Wilcoxon pareado por kata (within-subject) quando ha
     pares suficientes.
  5. DIFERENCIAL: intervalo de confianca da mediana por bootstrap, para
     mostrar a incerteza dado o N pequeno.

Uso:
  python analise_rq3.py                 # le metrics.csv, imprime o relatorio
  python analise_rq3.py --csv metrics.csv --out rq3_resultados.csv

Absorve automaticamente novos integrantes (ex.: Artur) assim que suas linhas
entram no metrics.csv - nao e preciso editar o script.
"""

import argparse

import numpy as np
import pandas as pd

try:
    from scipy.stats import wilcoxon
    TEM_SCIPY = True
except ImportError:
    TEM_SCIPY = False

# Metricas da RQ3. Para cada uma: se "menor e melhor" e se normaliza por LOC.
METRICAS = {
    "complexidade_media": {"rotulo": "Complexidade ciclomatica media", "por_loc": True},
    "duplicacao_pct":     {"rotulo": "Duplicacao (%)",                  "por_loc": False},
    "mi_medio":           {"rotulo": "Indice de Manutenibilidade (MI)", "por_loc": False},
    "loc":                {"rotulo": "LOC (controle)",                  "por_loc": False},
}


def iqr(serie):
    """Intervalo interquartil (Q3 - Q1)."""
    q1, q3 = np.percentile(serie, [25, 75])
    return q3 - q1


def bootstrap_ic_mediana(valores, n_reamostras=10000, conf=0.95, seed=42):
    """IC da mediana por bootstrap percentil. Devolve (baixo, alto).

    Reamostra os valores com reposicao muitas vezes, calcula a mediana de
    cada reamostra e toma os percentis. Robusto para N pequeno, onde a
    formula parametrica nao vale.
    """
    valores = np.asarray(valores, dtype=float)
    if len(valores) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    medianas = [
        np.median(rng.choice(valores, size=len(valores), replace=True))
        for _ in range(n_reamostras)
    ]
    alfa = (1 - conf) / 2
    return tuple(np.percentile(medianas, [100 * alfa, 100 * (1 - alfa)]))


def resumo_por_tratamento(df, coluna):
    """Mediana, IQR e IC-bootstrap de uma coluna, por tratamento."""
    linhas = []
    for trat in ["ia", "manual"]:
        vals = df.loc[df["tratamento"] == trat, coluna].dropna().values
        if len(vals) == 0:
            continue
        ic_baixo, ic_alto = bootstrap_ic_mediana(vals)
        linhas.append({
            "tratamento": trat,
            "n": len(vals),
            "mediana": float(np.median(vals)),
            "iqr": float(iqr(vals)),
            "ic95_baixo": ic_baixo,
            "ic95_alto": ic_alto,
        })
    return pd.DataFrame(linhas)


def wilcoxon_pareado(df, coluna):
    """Wilcoxon pareado por kata: para cada kata, pareia ia vs manual.

    Pareia pela MEDIANA dentro de cada (kata, tratamento), para o caso de
    mais de um integrante ter feito o mesmo kata no mesmo tratamento.
    """
    piv = (df.groupby(["kata", "tratamento"])[coluna]
             .median()
             .unstack("tratamento"))
    if "ia" not in piv or "manual" not in piv:
        return None
    pares = piv.dropna(subset=["ia", "manual"])
    if len(pares) < 2:
        return {"n_pares": len(pares), "p_valor": None,
                "nota": "pares insuficientes para Wilcoxon (precisa de >= 2)"}
    if not TEM_SCIPY:
        return {"n_pares": len(pares), "p_valor": None,
                "nota": "scipy nao instalado"}
    diffs = (pares["ia"] - pares["manual"]).values
    if np.allclose(diffs, 0):
        # ia e manual identicos em todos os pares: nao ha diferenca a testar
        return {"n_pares": len(pares), "p_valor": None,
                "nota": "diferencas todas nulas (ia == manual nos pares)"}
    try:
        _, p = wilcoxon(pares["ia"], pares["manual"])
        return {"n_pares": len(pares), "p_valor": float(p), "nota": ""}
    except ValueError as e:
        return {"n_pares": len(pares), "p_valor": None, "nota": str(e)}


def main():
    ap = argparse.ArgumentParser(description="Analise da RQ3 (estrutura do codigo).")
    ap.add_argument("--csv", default="metrics.csv", help="entrada (metrics.csv)")
    ap.add_argument("--out", default="rq3_resultados.csv",
                    help="CSV de saida com o resumo por metrica/tratamento")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df.columns = [c.strip() for c in df.columns]

    # LOC como controle: cria versoes normalizadas por 100 LOC onde faz sentido.
    for m, cfg in METRICAS.items():
        if cfg["por_loc"] and m in df.columns:
            df[m + "_por100loc"] = df[m] / df["loc"] * 100

    print("=" * 68)
    print("RQ3 - Estrutura do codigo: IA vs Manual")
    print(f"Integrantes: {', '.join(sorted(df['integrante'].unique()))}"
          f"  |  trials: {len(df)}")
    print("=" * 68)

    saida = []
    for m, cfg in METRICAS.items():
        if m not in df.columns:
            continue
        print(f"\n### {cfg['rotulo']}")
        res = resumo_por_tratamento(df, m)
        for _, r in res.iterrows():
            print(f"  {r['tratamento']:6s} | n={int(r['n'])} | "
                  f"mediana={r['mediana']:.2f} | IQR={r['iqr']:.2f} | "
                  f"IC95%[{r['ic95_baixo']:.2f}, {r['ic95_alto']:.2f}]")
            saida.append({"metrica": m, **r.to_dict()})

        w = wilcoxon_pareado(df, m)
        if w:
            if w["p_valor"] is not None:
                sig = "SIGNIFICATIVO" if w["p_valor"] < 0.05 else "nao significativo"
                print(f"  Wilcoxon pareado (n_pares={w['n_pares']}): "
                      f"p={w['p_valor']:.4f} -> {sig}")
            else:
                print(f"  Wilcoxon: {w['nota']}")

        # versao normalizada por LOC, quando aplicavel
        if cfg["por_loc"]:
            mn = m + "_por100loc"
            print(f"  -- normalizado por LOC ({cfg['rotulo']} por 100 LOC) --")
            resn = resumo_por_tratamento(df, mn)
            for _, r in resn.iterrows():
                print(f"     {r['tratamento']:6s} | mediana={r['mediana']:.3f} "
                      f"| IQR={r['iqr']:.3f}")

    pd.DataFrame(saida).to_csv(args.out, index=False)
    print(f"\nResumo salvo em {args.out}")
    print("\nLeitura: com N pequeno, o IC95% por bootstrap mostra a incerteza "
          "da mediana. In­tervalos que se sobrepoem entre ia e manual indicam "
          "que a diferenca observada pode nao ser real.")


if __name__ == "__main__":
    main()
