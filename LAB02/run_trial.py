#!/usr/bin/env python3
"""
run_trial.py - Executa um trial completo de ponta a ponta (Lab02).

Encadeia os tres scripts na ordem certa:
  1. timer.py    -> cronometra ate o green (ou censura em 35 min) -> trials.csv
  2. run_tests.py -> testes de aceitacao sobre o codigo final     -> tests.csv
  3. metrics.py   -> complexidade/MI/LOC/duplicacao                -> metrics.csv

Assim voce nao esquece nenhum passo no meio do cronometro: ligue o trial,
resolva o kata (com IA ou manual), e ao passar nos testes os outros dois
scripts rodam sozinhos.

Uso:
  python run_trial.py --integrante pedro --kata kata01 --tratamento ia
  python run_trial.py --integrante pedro --kata kata02 --tratamento manual --manual

O numero de testes esperado de cada kata e lido automaticamente do katas.json,
entao voce nao precisa passar --total-esperado na mao.
"""

import argparse
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def total_esperado_do_kata(kata):
    """Le testes_aceitacao do katas.json a partir do id no nome (kataNN)."""
    kid = int("".join(c for c in kata if c.isdigit()))
    with open(os.path.join(AQUI, "katas.json"), encoding="utf-8") as f:
        katas = json.load(f)["katas"]
    for k in katas:
        if k["id"] == kid:
            return k["testes_aceitacao"]
    raise SystemExit(f"Kata id {kid} nao encontrado no katas.json")


def run(cmd):
    print("\n$ " + " ".join(cmd))
    return subprocess.run(cmd).returncode


def main():
    p = argparse.ArgumentParser(description="Executa um trial completo.")
    p.add_argument("--integrante", required=True)
    p.add_argument("--kata", required=True, help="ex.: kata01")
    p.add_argument("--tratamento", required=True, choices=["ia", "manual"])
    p.add_argument("--manual", action="store_true",
                   help="cronometro manual (aperta ENTER no green) em vez de "
                        "rodar pytest em loop automaticamente")
    p.add_argument("--poll", type=int, default=5)
    args = p.parse_args()

    kata_dir = os.path.join(AQUI, "katas", args.kata)
    if not os.path.isdir(kata_dir):
        raise SystemExit(f"Pasta {kata_dir} nao existe.")

    total = total_esperado_do_kata(args.kata)
    py = sys.executable

    base = ["--integrante", args.integrante,
            "--kata", args.kata,
            "--tratamento", args.tratamento]

    # 1. cronometro
    timer_cmd = [py, os.path.join(AQUI, "timer.py"), *base,
                 "--csv", os.path.join(AQUI, "trials.csv")]
    if args.manual:
        pass  # timer entra em modo manual por padrao (sem --auto)
    else:
        timer_cmd += ["--auto", "--test-path", kata_dir, "--poll", str(args.poll)]

    print(f"=== TRIAL: {args.integrante} | {args.kata} | {args.tratamento} ===")
    print(f"Time-box: 35 min. Testes esperados neste kata: {total}.")
    run(timer_cmd)

    # 2. testes de aceitacao sobre o codigo final
    run([py, os.path.join(AQUI, "run_tests.py"), *base,
         "--test-path", kata_dir,
         "--total-esperado", str(total),
         "--csv", os.path.join(AQUI, "tests.csv")])

    # 3. metricas estaticas sobre a solucao
    run([py, os.path.join(AQUI, "metrics.py"), *base,
         "--src", os.path.join(kata_dir, "solucao.py"),
         "--csv", os.path.join(AQUI, "metrics.csv")])

    print("\n=== Trial concluido. Dados em trials.csv, tests.csv, metrics.csv ===")
    print("Agora: git add + commit da solucao referenciando a Issue deste trial.")


if __name__ == "__main__":
    main()
