"""
Kata 4 — Parser de log simplificado

Dado um conjunto de linhas de log no formato customizado "TIPO|mensagem"
(ex.: "INFO|usuário logado"), contar quantas linhas existem de cada TIPO.

Linhas que não seguem o formato (sem o caractere "|") devem ser ignoradas.

Exemplo:
    contar_eventos([
        "INFO|usuário logado",
        "ERROR|falha ao conectar",
        "INFO|página carregada",
        "linha invalida sem separador",
    ])
    -> {"INFO": 2, "ERROR": 1}
"""

def contar_eventos(linhas):
    contagem = {}
    for linha in linhas:
        if "|" not in linha:
            continue
        tipo, _ = linha.split("|", 1)
        contagem[tipo] = contagem.get(tipo, 0) + 1
    return contagem