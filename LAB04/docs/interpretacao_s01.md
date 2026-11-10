# Interpretação do resultado (S01)

Conjunto simulado gerado com `python -m src.testes` (semente 42, 30 PRs por grupo, lognormal com os parâmetros de `config/cenario.yaml`).
O grupo sem bot foi gerado com mediana de 8,3 h (σ = 2,42) e o grupo com bot com mediana de 1,6 h (σ = 2,00), ou seja, **existe efeito de verdade** nesse conjunto.

## Resultado

| Teste | Estatística | p-valor | Tamanho do efeito | Rejeita H₀ (α = 0,05)? |
|---|---|---|---|---|
| t de Welch | t = 2,49 | 0,017 | d de Cohen = 0,64 (médio) | Sim |
| Mann-Whitney | U = 664 | 0,0016 | delta de Cliff = 0,48 (grande) | Sim |

Medianas da amostra: 10,5 h (sem bot) e 2,2 h (com bot). Médias: 27,9 h e 7,8 h.

## O que cada teste concluiu e por quê

**Welch.** Compara as médias dos dois grupos. A média sem bot (27,9 h) é bem maior que a média com bot (7,8 h), e o teste rejeita H₀ com p = 0,017. Mesmo assim, o p-valor ficou perto do limite de 0,05. Como os dados são muito assimétricos, poucos PRs que demoram muito aumentam bastante a variância. Isso deixa o erro padrão grande e reduz a estatística t.

**Mann-Whitney.** Compara os postos, ou seja, se um PR do grupo sem bot tende a demorar mais que um do grupo com bot. Como usa a ordem e não o valor, os PRs muito demorados não inflam nada. Por isso o p-valor é cerca de 10 vezes menor (0,0016), e o delta de Cliff indica um efeito grande: na maior parte das comparações, o PR sem bot demorou mais.

**Conclusão.** Os dois testes acertaram nesse conjunto, porque o efeito existe e os dois rejeitaram H₀. O Mann-Whitney deu uma evidência bem mais forte, o que é um primeiro sinal de que ele tem mais poder com dados assimétricos como estes. Um único conjunto não prova isso: a S02 repete a simulação 10.000 vezes para medir com que frequência cada teste acerta.
