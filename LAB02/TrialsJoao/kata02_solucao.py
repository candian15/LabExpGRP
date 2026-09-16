def validar_senha(senha):
    senha_str = str(senha)
    
    if len(senha_str) < 10:
        return "comprimento"
        
    digitos = 0
    for caracter in senha_str:
        if caracter.isdigit():
            digitos += 1
            
    if digitos < 3:
        return "digitos"
        
    tem_maiuscula = False
    for caracter in senha_str:
        if caracter.isupper():
            tem_maiuscula = True
            
    if not tem_maiuscula:
        return "maiuscula"
        
    if " " in senha_str:
        return "simbolo_proibido"
        
    senha_minuscula = senha_str.lower()
    if "123" in senha_minuscula or "abc" in senha_minuscula:
        return "sequencia"
        
    return "ok"
