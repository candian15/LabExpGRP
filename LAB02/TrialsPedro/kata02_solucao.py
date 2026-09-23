REGRAS_SEQUENCIA = ("123", "abc")


def validar_senha(senha):
    """Retorna 'ok' ou o codigo da primeira regra violada.

    Ver especificacao do kata 2 em katas.json (campo "especificacao").
    A checagem para na primeira violacao, de cima para baixo.
    """
    if len(senha) < 10:
        return "comprimento"

    if sum(1 for caractere in senha if caractere.isdigit()) < 3:
        return "digitos"

    if not any(caractere.isupper() for caractere in senha):
        return "maiuscula"

    if any(caractere.isspace() for caractere in senha):
        return "simbolo_proibido"

    if any(sequencia in senha for sequencia in REGRAS_SEQUENCIA):
        return "sequencia"

    return "ok"
