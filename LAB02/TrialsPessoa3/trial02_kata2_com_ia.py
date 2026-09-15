"""
Kata 2 — Validador de senha customizado

Implementar validação de senha com as regras abaixo, retornando o NOME da
primeira regra violada (na ordem listada), ou "OK" se a senha passar em todas.

Regras (nesta ordem de checagem):
1. "muito_curta"        -> senha deve ter pelo menos 10 caracteres
2. "sem_digito"         -> senha deve conter pelo menos um dígito (0-9)
3. "sem_maiuscula"      -> senha deve conter pelo menos uma letra maiúscula
4. "repeticao_consecutiva" -> senha não pode ter 3 caracteres iguais seguidos (ex.: "aaa")
5. "sequencia_proibida" -> senha não pode conter a substring "1234"

Exemplo:
    validar_senha("abc")          -> "muito_curta"
    validar_senha("abcdefghij")   -> "sem_digito"
    validar_senha("Abcdefghij1")  -> "OK"
"""

def validar_senha(senha):
    if len(senha) < 10:
        return "muito_curta"

    if not any(c.isdigit() for c in senha):
        return "sem_digito"

    if not any(c.isupper() for c in senha):
        return "sem_maiuscula"

    for i in range(len(senha) - 2):
        if senha[i] == senha[i + 1] == senha[i + 2]:
            return "repeticao_consecutiva"

    if "1234" in senha:
        return "sequencia_proibida"

    return "OK"