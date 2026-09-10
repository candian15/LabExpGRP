"""
Validação da seleção de katas — Lab02S01

Verifica se a lista de katas escolhida atende aos critérios do enunciado:
- número par de katas (permite divisão exata entre trials com/sem IA)
- dificuldade comparável entre todos os katas
- todos com justificativa de baixa indexação preenchida
- todos com testes de aceitação definidos (>= 1)

Uso:
    python validate_katas.py katas.json
"""

import sys
import json
from collections import Counter


def load_katas(filename):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    return data["katas"]


def validate(katas):
    problems = []

    # 1. número par
    if len(katas) % 2 != 0:
        problems.append(f"Número de katas é ímpar ({len(katas)}) — precisa ser par.")

    # 2. dificuldade comparável (todas iguais, ou dentro de no máximo 2 níveis distintos)
    dificuldades = Counter(k["dificuldade"] for k in katas)
    if len(dificuldades) > 2:
        problems.append(
            f"Muitos níveis de dificuldade distintos: {dict(dificuldades)} — "
            "recomenda-se manter os katas em um único nível para comparabilidade."
        )

    # 3. justificativa de baixa indexação
    for k in katas:
        if not k.get("justificativa_baixa_indexacao", "").strip():
            problems.append(f"Kata #{k['id']} ({k['titulo']}) sem justificativa de baixa indexação.")

    # 4. testes de aceitação definidos
    for k in katas:
        if k.get("testes_aceitacao", 0) < 1:
            problems.append(f"Kata #{k['id']} ({k['titulo']}) sem testes de aceitação definidos.")

    # 5. LOC de referência dentro de uma faixa razoável (evita katas muito desbalanceados em tamanho)
    locs = [k.get("loc_estimado_referencia", 0) for k in katas]
    if locs and (max(locs) - min(locs)) > 30:
        problems.append(
            f"Variação grande de tamanho estimado entre katas (min={min(locs)}, max={max(locs)} LOC) — "
            "considere ajustar para reduzir viés de tamanho entre trials."
        )

    return problems


def print_summary(katas):
    print(f"Total de katas: {len(katas)}\n")
    print(f"{'ID':<4}{'Título':<45}{'Dificuldade':<12}{'Testes':<8}{'LOC~':<6}")
    print("-" * 75)
    for k in katas:
        print(f"{k['id']:<4}{k['titulo']:<45}{k['dificuldade']:<12}"
              f"{k['testes_aceitacao']:<8}{k['loc_estimado_referencia']:<6}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python validate_katas.py <katas.json>")
        sys.exit(1)

    katas = load_katas(sys.argv[1])
    print_summary(katas)

    problems = validate(katas)
    print("\n--- Validação ---")
    if not problems:
        print("OK: seleção de katas atende a todos os critérios do enunciado.")
    else:
        print(f"{len(problems)} ponto(s) de atenção encontrados:")
        for p in problems:
            print(f" - {p}")


if __name__ == "__main__":
    main()
