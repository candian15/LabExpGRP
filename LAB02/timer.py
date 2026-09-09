#!/usr/bin/env python3
"""
timer.py - Cronometragem e coleta de tempo dos trials (Lab02 - Pessoa 1)

Cobre as 3 Issues da S01:
  - Issue 1: cronometro com time-box de 35 min e censura automatica.
  - Issue 2: deteccao automatica de "time-to-green" rodando pytest em loop.
  - Issue 3: gravacao de cada trial em trials.csv com o schema combinado.

Uso:
  # Modo automatico: roda pytest ate todos passarem (ou censura em 35 min)
  python timer.py --integrante pedro --kata kata01 --tratamento ia \\
      --auto --test-path katas/kata01

  # Modo manual: aperte ENTER quando os testes passarem
  python timer.py --integrante pedro --kata kata01 --tratamento manual

Schema do trials.csv:
  integrante, kata, tratamento, tempo_segundos, censurado, timestamp
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime

# Time-box fixo da disciplina. Pode ser REDUZIDO, nunca aumentado.
TIME_BOX_SECONDS = 35 * 60  # 2100 s

CSV_HEADER = [
    "integrante",
    "kata",
    "tratamento",
    "tempo_segundos",
    "censurado",
    "timestamp",
]


def run_pytest(test_path):
    """Roda pytest no caminho dado. Retorna True se todos os testes passaram."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-q"],
        capture_output=True,
        text=True,
    )
    # pytest retorna 0 quando todos os testes passam.
    return result.returncode == 0


def fmt(seconds):
    """Formata segundos como MM:SS para exibir no terminal."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def run_auto(test_path, poll_interval):
    """Modo automatico: roda pytest em loop ate green ou ate o time-box.

    Retorna (tempo_segundos, censurado).
    """
    print(f"Modo AUTOMATICO. Rodando pytest em '{test_path}' a cada "
          f"{poll_interval}s. Time-box: {fmt(TIME_BOX_SECONDS)}.\n")
    start = time.monotonic()
    while True:
        elapsed = time.monotonic() - start

        if elapsed >= TIME_BOX_SECONDS:
            print(f"\n[{fmt(TIME_BOX_SECONDS)}] Time-box atingido. "
                  f"Trial CENSURADO.")
            return TIME_BOX_SECONDS, True

        if run_pytest(test_path):
            elapsed = time.monotonic() - start
            print(f"\n[{fmt(elapsed)}] GREEN! Todos os testes passaram.")
            return round(elapsed, 2), False

        print(f"[{fmt(elapsed)}] testes ainda falhando...", end="\r")

        # Nao ultrapassa o time-box esperando o proximo ciclo.
        restante = TIME_BOX_SECONDS - (time.monotonic() - start)
        if restante <= 0:
            print(f"\n[{fmt(TIME_BOX_SECONDS)}] Time-box atingido. "
                  f"Trial CENSURADO.")
            return TIME_BOX_SECONDS, True
        time.sleep(min(poll_interval, restante))


def run_manual():
    """Modo manual: cronometra ate o usuario apertar ENTER ou o time-box.

    Retorna (tempo_segundos, censurado).
    """
    print(f"Modo MANUAL. Aperte ENTER quando os testes passarem. "
          f"Time-box: {fmt(TIME_BOX_SECONDS)}.\n")
    start = time.monotonic()

    # Espera ENTER com timeout via select (funciona em Linux/Mac).
    try:
        import select
        ready, _, _ = select.select([sys.stdin], [], [], TIME_BOX_SECONDS)
        elapsed = time.monotonic() - start
        if ready:
            sys.stdin.readline()
            if elapsed >= TIME_BOX_SECONDS:
                return TIME_BOX_SECONDS, True
            print(f"\n[{fmt(elapsed)}] GREEN registrado manualmente.")
            return round(elapsed, 2), False
        else:
            print(f"\n[{fmt(TIME_BOX_SECONDS)}] Time-box atingido. "
                  f"Trial CENSURADO.")
            return TIME_BOX_SECONDS, True
    except (ImportError, OSError):
        # Fallback sem timeout (Windows): apenas espera o ENTER.
        input("Pressione ENTER ao ver o green: ")
        elapsed = time.monotonic() - start
        if elapsed >= TIME_BOX_SECONDS:
            return TIME_BOX_SECONDS, True
        return round(elapsed, 2), False


def append_trial(row, csv_path):
    """Grava (append) um trial no CSV, criando o header se preciso."""
    novo = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)
    print(f"Trial gravado em {os.path.abspath(csv_path)}: {row}")


def main():
    parser = argparse.ArgumentParser(
        description="Cronometra um trial e grava em trials.csv."
    )
    parser.add_argument("--integrante", required=True,
                        help="nome/identificador do integrante")
    parser.add_argument("--kata", required=True,
                        help="identificador do kata, ex.: kata01")
    parser.add_argument("--tratamento", required=True, choices=["ia", "manual"],
                        help="tratamento do trial: com IA ou codificacao manual")
    parser.add_argument("--auto", action="store_true",
                        help="modo automatico: detecta green rodando pytest")
    parser.add_argument("--test-path", default=".",
                        help="caminho dos testes de aceitacao (modo --auto)")
    parser.add_argument("--poll", type=int, default=5,
                        help="intervalo em segundos entre execucoes do pytest")
    parser.add_argument("--csv", default="trials.csv",
                        help="caminho do CSV de saida (padrao: trials.csv no "
                             "diretorio atual). Use um caminho fixo para "
                             "juntar todos os trials no mesmo arquivo.")
    args = parser.parse_args()

    if args.auto:
        tempo, censurado = run_auto(args.test_path, args.poll)
    else:
        tempo, censurado = run_manual()

    row = [
        args.integrante,
        args.kata,
        args.tratamento,
        tempo,
        str(censurado).lower(),   # "true"/"false"
        datetime.now().isoformat(timespec="seconds"),
    ]
    append_trial(row, args.csv)


if __name__ == "__main__":
    main()
