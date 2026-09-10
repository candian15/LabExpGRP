#!/usr/bin/env python3
"""
metrics.py - Metricas estaticas do codigo final de cada trial (Lab02 - RQ3)

Roda sobre o codigo entregue em um trial e grava uma linha em metrics.csv:
  - complexidade ciclomatica media (McCabe) por funcao/metodo -> radon cc
  - Indice de Manutenibilidade medio por arquivo             -> radon mi
  - LOC e SLOC (metrica de controle, obrigatoria)            -> radon raw
  - % de linhas duplicadas                                   -> jscpd

Uso:
  python metrics.py --integrante joao --kata kata01 --tratamento ia \\
      --src katas/kata01/solucao.py

  # sem duplicacao (quando jscpd/npx nao estiver disponivel)
  python metrics.py --integrante joao --kata kata01 --tratamento manual \\
      --src katas/kata01 --sem-jscpd

Schema do metrics.csv:
  integrante, kata, tratamento, arquivos, loc, sloc, complexidade_media,
  mi_medio, duplicacao_pct, timestamp
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

CSV_HEADER = [
    "integrante",
    "kata",
    "tratamento",
    "arquivos",
    "loc",
    "sloc",
    "complexidade_media",
    "mi_medio",
    "duplicacao_pct",
    "timestamp",
]


def run_radon(comando, src):
    """Roda 'radon <comando> -j <src>' e devolve o JSON como dict."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", comando, "-j", src],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        print(f"AVISO: 'radon {comando}' falhou em '{src}'. "
              f"Instale com: pip install -r requirements.txt")
        print(result.stderr.strip())
        return {}
    return json.loads(result.stdout)


def coletar_complexidade(src):
    """Complexidade ciclomatica media entre todos os blocos (funcoes/metodos).

    Retorna (media, n_arquivos). Arquivo sem funcao nenhuma nao entra na media.
    """
    dados = run_radon("cc", src)
    complexidades = []
    arquivos = 0
    for nome, blocos in dados.items():
        # Em caso de erro de sintaxe o radon devolve um dict, nao uma lista.
        # Isso e comum em trial censurado, cujo codigo ficou pela metade.
        if not isinstance(blocos, list):
            erro = blocos.get("error", "erro desconhecido") if isinstance(blocos, dict) else ""
            print(f"AVISO: o radon nao conseguiu analisar '{nome}': {erro}")
            continue
        arquivos += 1
        for bloco in blocos:
            complexidades.append(bloco["complexity"])
    if not complexidades:
        return None, arquivos
    return round(sum(complexidades) / len(complexidades), 2), arquivos


def coletar_mi(src):
    """Indice de Manutenibilidade medio entre os arquivos analisados."""
    dados = run_radon("mi", src)
    valores = [v["mi"] for v in dados.values() if isinstance(v, dict) and "mi" in v]
    if not valores:
        return None
    return round(sum(valores) / len(valores), 2)


def coletar_loc(src):
    """LOC (linhas totais) e SLOC (linhas de codigo, sem branco/comentario).

    Retorna (None, None) quando nenhum arquivo pode ser lido, para nao gravar
    zero (que significaria "arquivo vazio") no lugar de "nao medido".
    """
    dados = run_radon("raw", src)
    loc = sloc = 0
    lidos = 0
    for v in dados.values():
        if isinstance(v, dict) and "loc" in v:
            loc += v["loc"]
            sloc += v["sloc"]
            lidos += 1
    if lidos == 0:
        return None, None
    return loc, sloc


def coletar_duplicacao(src, min_tokens):
    """% de linhas duplicadas via jscpd. Retorna None se a ferramenta faltar.

    O padrao do jscpd (50 tokens) e alto demais para katas curtos e faz tudo
    dar 0%. Usamos 30, valor fixo para todos os trials (ver README).
    """
    if shutil.which("jscpd"):
        base = ["jscpd"]
    elif shutil.which("npx"):
        base = ["npx", "--yes", "jscpd"]
    else:
        print("AVISO: jscpd/npx nao encontrados. Duplicacao ficara vazia. "
              "Instale com: npm install -g jscpd")
        return None

    with tempfile.TemporaryDirectory() as saida:
        result = subprocess.run(
            base + [src, "--reporters", "json", "--output", saida,
                    "--format", "python", "--min-tokens", str(min_tokens),
                    "--silent"],
            capture_output=True,
            text=True,
        )
        relatorio = os.path.join(saida, "jscpd-report.json")
        if not os.path.exists(relatorio):
            print("AVISO: jscpd nao gerou relatorio. Duplicacao ficara vazia.")
            print(result.stderr.strip())
            return None
        with open(relatorio, encoding="utf-8") as f:
            dados = json.load(f)
    return round(dados["statistics"]["total"]["percentage"], 2)


def append_metrics(row, csv_path):
    """Grava (append) uma linha de metricas no CSV, criando o header se preciso."""
    novo = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)
    print(f"Metricas gravadas em {os.path.abspath(csv_path)}: {row}")


def main():
    parser = argparse.ArgumentParser(
        description="Coleta metricas estaticas de um trial e grava em metrics.csv."
    )
    parser.add_argument("--integrante", required=True,
                        help="nome/identificador do integrante")
    parser.add_argument("--kata", required=True,
                        help="identificador do kata, ex.: kata01")
    parser.add_argument("--tratamento", required=True, choices=["ia", "manual"],
                        help="tratamento do trial: com IA ou codificacao manual")
    parser.add_argument("--src", required=True,
                        help="arquivo ou pasta com o codigo final do trial "
                             "(so a solucao, sem os arquivos de teste)")
    parser.add_argument("--sem-jscpd", action="store_true",
                        help="pula a medicao de duplicacao")
    parser.add_argument("--min-tokens", type=int, default=30,
                        help="tamanho minimo do clone para o jscpd (padrao: 30). "
                             "Mantenha o mesmo valor em todos os trials.")
    parser.add_argument("--csv", default="metrics.csv",
                        help="caminho do CSV de saida (padrao: metrics.csv no "
                             "diretorio atual). Use um caminho fixo para juntar "
                             "todos os trials no mesmo arquivo.")
    args = parser.parse_args()

    if not os.path.exists(args.src):
        parser.error(f"caminho nao encontrado: {args.src}")

    complexidade, arquivos = coletar_complexidade(args.src)
    mi = coletar_mi(args.src)
    loc, sloc = coletar_loc(args.src)
    duplicacao = (None if args.sem_jscpd
                  else coletar_duplicacao(args.src, args.min_tokens))

    if arquivos == 0:
        print("AVISO: nenhum arquivo Python valido foi analisado. As metricas "
              "vao para o CSV vazias (= nao medido), nao como zero.")

    row = [
        args.integrante,
        args.kata,
        args.tratamento,
        arquivos,
        "" if loc is None else loc,
        "" if sloc is None else sloc,
        "" if complexidade is None else complexidade,
        "" if mi is None else mi,
        "" if duplicacao is None else duplicacao,
        datetime.now().isoformat(timespec="seconds"),
    ]
    append_metrics(row, args.csv)


if __name__ == "__main__":
    main()
