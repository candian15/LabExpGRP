"""Leitura das taxas de rejeição gravadas em ``resultados/``.

Q1, Q2 e Q3 gravam a mesma tabela (uma linha por situação, razão e teste), cada uma em
seu arquivo. O G3 e o G4 precisam das três juntas, então quem lê é este módulo: os
gráficos recebem a tabela pronta e não sabem de onde ela veio, e o dashboard e o
``rodar_tudo`` usam exatamente a mesma leitura.

Uso (a partir de LAB04/):  python -m src.resultados
"""
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent.parent / "resultados"

# Ordem da leitura e também a dos gráficos. Q1 vem antes de Q2 de propósito: as duas
# simulações têm a linha de razão = 1 no cenário real, e a estimativa que vale é a da
# Q1, que gastou as 10.000 repetições só nela.
ARQUIVOS = ("q1.csv", "q2.csv", "q3.csv")
COLUNAS = ("situacao", "n", "sigma", "razao", "teste", "taxa_rejeicao")
CHAVE = ["situacao", "n", "sigma", "razao", "teste"]

SEM_EFEITO = 1.0  # razão entre as medianas com H₀ verdadeira

# A cor de cada teste, definida aqui e em mais lugar nenhum: o enunciado pede a mesma
# cor para o mesmo teste em todos os gráficos, e as figuras do matplotlib e a página
# publicada são desenhadas por módulos diferentes. A ordem também vale: é a ordem em
# que os dois testes aparecem nas barras e nas legendas.
CORES = {"Welch": "#e8590c", "Mann-Whitney": "#2563eb"}

# As situações da Q3 saem do docs/cenario.md. A situação que não estiver aqui ainda
# aparece nos gráficos, no fim da ordem e com o nome que vier do CSV.
ORDEM = ("real", "bem_comportada", "n_pequeno", "outliers")
NOMES = {
    "real": "cenário real",
    "bem_comportada": "bem comportada",
    "n_pequeno": "amostra pequena",
    "outliers": "com outliers",
}


def ler_taxas(pasta=PASTA) -> pd.DataFrame:
    """Junta q1.csv, q2.csv e q3.csv em uma tabela só, na ordem de ``ORDEM``.

    Ignora os arquivos que ainda não existem — é o que mantém o G3 e o G4 de pé
    enquanto a Q3 não está pronta. Levanta ``FileNotFoundError`` se não houver nenhum.
    """
    pasta = Path(pasta)
    partes = [pd.read_csv(pasta / nome) for nome in ARQUIVOS if (pasta / nome).is_file()]
    if not partes:
        raise FileNotFoundError(
            f"nenhum resultado em {pasta}; rode `python -m src.rodar_tudo` antes"
        )

    taxas = pd.concat(partes, ignore_index=True)
    faltando = [c for c in COLUNAS if c not in taxas.columns]
    if faltando:
        raise ValueError(f"os resultados estão sem a(s) coluna(s) {faltando}")

    taxas = taxas.drop_duplicates(subset=CHAVE, keep="first")
    return ordenar(taxas)


def situacoes(taxas: pd.DataFrame) -> list[str]:
    """As situações presentes na tabela, na ordem em que devem aparecer nos gráficos."""
    presentes = list(dict.fromkeys(taxas["situacao"]))
    conhecidas = [s for s in ORDEM if s in presentes]
    return conhecidas + sorted(s for s in presentes if s not in ORDEM)


def ordenar(taxas: pd.DataFrame) -> pd.DataFrame:
    """Situação na ordem de ``ORDEM`` e, dentro de cada uma, efeito crescente."""
    ordem = situacoes(taxas)
    posicao = taxas["situacao"].map(ordem.index)
    return (taxas.assign(_pos=posicao)
            .sort_values(["_pos", "razao", "teste"], ascending=[True, False, True])
            .drop(columns="_pos")
            .reset_index(drop=True))


def erro_tipo_i(taxas: pd.DataFrame) -> pd.DataFrame:
    """Só as linhas de H₀ verdadeira (razão = 1), que é o que o G3 mostra."""
    return taxas[taxas["razao"] == SEM_EFEITO].reset_index(drop=True)


def nome(situacao: str, n=None, sigma=None) -> str:
    """Rótulo da situação para o eixo e para o título do painel."""
    rotulo = NOMES.get(situacao, str(situacao).replace("_", " "))
    if n is None and sigma is None:
        return rotulo
    detalhe = []
    if sigma is not None:
        detalhe.append(f"σ = {float(sigma):.2f}".replace(".", ","))
    if n is not None:
        detalhe.append(f"n = {int(n)}")
    return f"{rotulo}\n({'; '.join(detalhe)})"


def rotulos(taxas: pd.DataFrame) -> list[str]:
    """Um rótulo por situação, já com o n e o σ que foram usados nela."""
    saida = []
    for s in situacoes(taxas):
        linha = taxas[taxas["situacao"] == s].iloc[0]
        saida.append(nome(s, linha["n"], linha["sigma"]))
    return saida


if __name__ == "__main__":
    taxas = ler_taxas()
    print(f"{len(taxas)} linhas, situações: {', '.join(situacoes(taxas))}\n")
    print("Erro tipo I (razão = 1):")
    print(erro_tipo_i(taxas).to_string(index=False))
