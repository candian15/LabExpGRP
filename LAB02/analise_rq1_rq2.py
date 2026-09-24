#!/usr/bin/env python3
"""
analise_rq1_rq2.py - Analise da RQ1 (tempo) e RQ2 (defeitos) - Lab02

RQ1: O uso de assistente de IA reduz o tempo necessario para resolver uma
     tarefa de programacao?
RQ2: O uso de assistente de IA reduz a quantidade de defeitos (testes que
     falham) no codigo produzido?

O que este script faz:
  1. Le trials.csv (tempo_segundos, censurado) e tests.csv (taxa_sucesso,
     testes_falhando) e junta pela chave (integrante, kata, tratamento).
  2. Compara os tratamentos 'ia' vs 'manual' usando MEDIANA e IQR (robusto
     ao N pequeno, como o enunciado pede).
  3. Aplica o teste de Wilcoxon PAREADO por (integrante, kata) - cada pessoa
     e seu proprio controle, condizente com o desenho crossover/within-subject.
  4. Reporta trials censurados (que bateram no time-box de 35 min) a parte,
     ja que censura e tratada como 2100 s, nao descartada.
  5. Intervalo de confianca da mediana por bootstrap, para mostrar a
     incerteza dado o N pequeno (mesmo tratamento usado no analise_rq3.py).

Uso:
  python analise_rq1_rq2.py
  python analise_rq1_rq2.py --trials trials.csv --tests tests.csv \
      --out-rq1 rq1_resultados.csv --out-rq2 rq2_resultados.csv

Absorve automaticamente novos integrantes (ex.: Artur) assim que suas linhas
entram em trials.csv/tests.csv - nao e preciso editar o script.
"""

import argparse

import numpy as np
import pandas as pd

try:
    from scipy.stats import wilcoxon
    TEM_SCIPY = True
except ImportError:
    TEM_SCIPY = False

CHAVE = ["integrante", "kata", "tratamento"]


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
    """Wilcoxon pareado por (integrante, kata): pareia ia vs manual.

    O desenho e crossover/within-subject: cada integrante resolve o MESMO
    conjunto de katas, metade com IA e metade sem. Para RQ1/RQ2, cada
    integrante contribui varios katas (nao o mesmo kata nos dois
    tratamentos), entao o pareamento aqui e por INTEGRANTE: a mediana de
    'coluna' nos katas 'ia' desse integrante vs. a mediana nos katas
    'manual' desse integrante. Isso preserva o "cada pessoa e seu proprio
    controle" mesmo sem repetir o mesmo kata nos dois tratamentos.
    """
    piv = (df.groupby(["integrante", "tratamento"])[coluna]
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
        return {"n_pares": len(pares), "p_valor": None,
                "nota": "diferencas todas nulas (ia == manual nos pares)"}
    try:
        _, p = wilcoxon(pares["ia"], pares["manual"])
        return {"n_pares": len(pares), "p_valor": float(p), "nota": ""}
    except ValueError as e:
        return {"n_pares": len(pares), "p_valor": None, "nota": str(e)}


def carregar_dados(trials_path, tests_path):
    """Le e junta trials.csv + tests.csv pela chave (integrante, kata, tratamento)."""
    trials = pd.read_csv(trials_path)
    tests = pd.read_csv(tests_path)
    trials.columns = [c.strip() for c in trials.columns]
    tests.columns = [c.strip() for c in tests.columns]

    df = pd.merge(trials, tests, on=CHAVE, how="outer", suffixes=("_trial", "_test"))
    faltando = df[df["tempo_segundos"].isna() | df["taxa_sucesso"].isna()]
    if not faltando.empty:
        print("AVISO: trials sem par completo em trials.csv/tests.csv (ignorados nas medias):")
        print(faltando[CHAVE].to_string(index=False))
    return df


def relatar_censura(df):
    """Lista trials censurados (bateram no time-box de 35 min = 2100 s)."""
    if "censurado" not in df.columns:
        return
    censurados = df[df["censurado"].astype(str).str.lower() == "true"]
    print(f"\nTrials censurados (time-box de 35 min atingido): {len(censurados)}")
    if len(censurados):
        print(censurados[CHAVE + ["tempo_segundos"]].to_string(index=False))
        print("Nota: censura e registrada como 2100 s, NAO descartada da analise "
              "(descartar distorceria a comparacao a favor do tratamento com "
              "mais falhas).")


def analisar_rq1(df, out_path):
    print("=" * 68)
    print("RQ1 - Tempo ate passar em todos os testes (time-to-green): IA vs Manual")
    print("=" * 68)

    res = resumo_por_tratamento(df, "tempo_segundos")
    saida = []
    for _, r in res.iterrows():
        print(f"  {r['tratamento']:6s} | n={int(r['n'])} | "
              f"mediana={r['mediana']:.1f}s ({r['mediana']/60:.2f} min) | "
              f"IQR={r['iqr']:.1f}s | IC95%[{r['ic95_baixo']:.1f}, {r['ic95_alto']:.1f}]s")
        saida.append({"metrica": "tempo_segundos", **r.to_dict()})

    w = wilcoxon_pareado(df, "tempo_segundos")
    if w:
        if w["p_valor"] is not None:
            sig = "SIGNIFICATIVO" if w["p_valor"] < 0.05 else "nao significativo"
            print(f"  Wilcoxon pareado por integrante (n_pares={w['n_pares']}): "
                  f"p={w['p_valor']:.4f} -> {sig}")
        else:
            print(f"  Wilcoxon: {w['nota']}")

    relatar_censura(df)

    pd.DataFrame(saida).to_csv(out_path, index=False)
    print(f"\nResumo da RQ1 salvo em {out_path}")


def analisar_rq2(df, out_path):
    print("\n" + "=" * 68)
    print("RQ2 - Defeitos (taxa de sucesso dos testes de aceitacao): IA vs Manual")
    print("=" * 68)

    saida = []
    for coluna, rotulo in [("taxa_sucesso", "Taxa de sucesso (%)"),
                           ("testes_falhando", "Testes falhando (absoluto)")]:
        if coluna not in df.columns:
            continue
        print(f"\n### {rotulo}")
        res = resumo_por_tratamento(df, coluna)
        for _, r in res.iterrows():
            print(f"  {r['tratamento']:6s} | n={int(r['n'])} | "
                  f"mediana={r['mediana']:.2f} | IQR={r['iqr']:.2f} | "
                  f"IC95%[{r['ic95_baixo']:.2f}, {r['ic95_alto']:.2f}]")
            saida.append({"metrica": coluna, **r.to_dict()})

        w = wilcoxon_pareado(df, coluna)
        if w:
            if w["p_valor"] is not None:
                sig = "SIGNIFICATIVO" if w["p_valor"] < 0.05 else "nao significativo"
                print(f"  Wilcoxon pareado por integrante (n_pares={w['n_pares']}): "
                      f"p={w['p_valor']:.4f} -> {sig}")
            else:
                print(f"  Wilcoxon: {w['nota']}")

    pd.DataFrame(saida).to_csv(out_path, index=False)
    print(f"\nResumo da RQ2 salvo em {out_path}")


def main():
    ap = argparse.ArgumentParser(
        description="Analise estatistica da RQ1 (tempo) e RQ2 (defeitos)."
    )
    ap.add_argument("--trials", default="trials.csv", help="entrada (trials.csv)")
    ap.add_argument("--tests", default="tests.csv", help="entrada (tests.csv)")
    ap.add_argument("--out-rq1", default="rq1_resultados.csv",
                    help="CSV de saida com o resumo da RQ1")
    ap.add_argument("--out-rq2", default="rq2_resultados.csv",
                    help="CSV de saida com o resumo da RQ2")
    args = ap.parse_args()

    df = carregar_dados(args.trials, args.tests)

    print(f"Integrantes: {', '.join(sorted(df['integrante'].dropna().unique()))}"
          f"  |  trials: {len(df)}")

    analisar_rq1(df, args.out_rq1)
    analisar_rq2(df, args.out_rq2)

    print("\nLeitura: com N pequeno, o IC95% por bootstrap mostra a incerteza da "
          "mediana. Intervalos que se sobrepoem entre ia e manual indicam que a "
          "diferenca observada pode nao ser real. O teste de Wilcoxon pareado "
          "confirma (ou nao) isso formalmente, respeitando o desenho "
          "within-subject (cada integrante e seu proprio controle).")


if __name__ == "__main__":
    main()
