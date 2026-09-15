"""
Kata 5 — Deduplicador de contatos com regras difusas

Dada uma lista de nomes de contato (strings), agrupar os que são "equivalentes"
segundo as regras abaixo, retornando uma lista de grupos (cada grupo é uma
lista com os nomes originais, na ordem em que apareceram).

Regras de equivalência (aplicadas antes de comparar):
1. Converter para minúsculas.
2. Remover espaços extras (múltiplos espaços viram um só; remover espaços
   nas pontas).
3. Substituir abreviações conhecidas por extenso, como palavra inteira:
   "jr" -> "junior", "sr" -> "senior".
   (ex.: "Carlos Jr" e "carlos junior" são equivalentes)

Exemplo:
    deduplicar_contatos(["Carlos Jr", "ANA", "carlos junior", "ana"])
    -> [["Carlos Jr", "carlos junior"], ["ANA", "ana"]]
"""


import re


def normalizar(nome):
    nome = nome.lower().strip()

    nome = re.sub(r"\s+", " ", nome)

    palavras = []
    for palavra in nome.split():
        if palavra == "jr":
            palavras.append("junior")
        elif palavra == "sr":
            palavras.append("senior")
        else:
            palavras.append(palavra)

    return " ".join(palavras)


def deduplicar_contatos(nomes):
    grupos = []
    mapa = {}

    for nome in nomes:
        chave = normalizar(nome)

        if chave not in mapa:
            mapa[chave] = len(grupos)
            grupos.append([])

        grupos[mapa[chave]].append(nome)

    return grupos