#!/usr/bin/env python3
"""
run_tests.py - Testes de aceitacao ao final do time-box (Lab02 - RQ2)

Roda o pytest sobre os testes de aceitacao de um trial e grava em tests.csv
o numero de testes passando/falhando e a taxa de sucesso (%), que e a metrica
primaria da RQ2 (normaliza katas com quantidades diferentes de testes).

Deve ser rodado sobre o codigo final do trial, ou seja, depois que o
timer.py encerrou o trial (green ou censura em 35 min).

Uso:
  python run_tests.py --integrante joao --kata kata01 --tratamento ia \\
      --test-path katas/kata01

Schema do tests.csv:
  integrante, kata, tratamento, testes_total, testes_passando,
  testes_falhando, taxa_sucesso, timestamp
"""

import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import datetime

CSV_HEADER = [
    "integrante",
    "kata",
    "tratamento",
    "testes_total",
    "testes_passando",
    "testes_falhando",
    "taxa_sucesso",
    "timestamp",
]

# Conta cada resultado na linha de resumo do pytest, ex.: "2 failed, 3 passed in 0.1s".
PADRAO_RESUMO = re.compile(r"(\d+) (passed|failed|errors?)")


def run_pytest(test_path):
    """Roda o pytest e devolve (passando, falhando, erro_de_coleta).

    So a ULTIMA linha da saida e lida. Ler a saida inteira contava o mesmo
    erro duas vezes ("Interrupted: 1 error during collection" e "1 error in
    0.11s" casam com o mesmo padrao).
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
    )
    saida = result.stdout + result.stderr
    print(saida)

    # Erro de coleta = o pytest nem chegou a rodar os testes (ex.: a solucao
    # tem erro de sintaxe). O total reportado nao vale como denominador.
    erro_de_coleta = "error during collection" in saida

    linhas = [l for l in saida.strip().splitlines() if l.strip()]
    resumo = linhas[-1] if linhas else ""

    passando = falhando = 0
    for quantidade, tipo in PADRAO_RESUMO.findall(resumo):
        if tipo == "passed":
            passando += int(quantidade)
        else:
            # failed e error(s) contam igual: teste de aceitacao que nao passou.
            falhando += int(quantidade)
    return passando, falhando, erro_de_coleta


def append_tests(row, csv_path):
    """Grava (append) um resultado no CSV, criando o header se preciso."""
    novo = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)
    print(f"Resultado gravado em {os.path.abspath(csv_path)}: {row}")


def main():
    parser = argparse.ArgumentParser(
        description="Roda os testes de aceitacao de um trial e grava em tests.csv."
    )
    parser.add_argument("--integrante", required=True,
                        help="nome/identificador do integrante")
    parser.add_argument("--kata", required=True,
                        help="identificador do kata, ex.: kata01")
    parser.add_argument("--tratamento", required=True, choices=["ia", "manual"],
                        help="tratamento do trial: com IA ou codificacao manual")
    parser.add_argument("--test-path", default=".",
                        help="caminho dos testes de aceitacao do kata")
    parser.add_argument("--total-esperado", type=int,
                        help="numero de testes de aceitacao do kata. Fixa o "
                             "denominador da taxa de sucesso, necessario "
                             "quando a solucao quebra e o pytest nao consegue "
                             "coletar todos os testes.")
    parser.add_argument("--csv", default="tests.csv",
                        help="caminho do CSV de saida (padrao: tests.csv no "
                             "diretorio atual). Use um caminho fixo para juntar "
                             "todos os trials no mesmo arquivo.")
    args = parser.parse_args()

    passando, falhando, erro_de_coleta = run_pytest(args.test_path)
    total = passando + falhando

    if erro_de_coleta:
        print("\nAVISO: o pytest falhou na coleta (a solucao provavelmente nao "
              "importa). Os testes nao chegaram a rodar.")

    if args.total_esperado:
        if total != args.total_esperado:
            print(f"AVISO: o pytest contabilizou {total} resultado(s), mas o "
                  f"kata tem {args.total_esperado} testes. Usando "
                  f"{args.total_esperado} como denominador.")
        total = args.total_esperado
        falhando = total - passando
    elif total == 0:
        print("ERRO: o pytest nao coletou nenhum teste. Confira o --test-path "
              "ou informe --total-esperado.")
        sys.exit(1)
    elif erro_de_coleta:
        print("ERRO: sem --total-esperado nao da para calcular a taxa de "
              "sucesso apos um erro de coleta (o denominador seria o numero "
              "de erros, nao o de testes do kata).")
        sys.exit(1)

    taxa = round(100 * passando / total, 2)
    print(f"\n{passando}/{total} testes passando - taxa de sucesso: {taxa}%")

    row = [
        args.integrante,
        args.kata,
        args.tratamento,
        total,
        passando,
        falhando,
        taxa,
        datetime.now().isoformat(timespec="seconds"),
    ]
    append_tests(row, args.csv)


if __name__ == "__main__":
    main()
