# Interpretação do resultado (S01)

Conjunto simulado gerado com `python -m src.testes` (semente 42, 30 PRs por grupo, lognormal).
No cenário usado, o grupo sem bot tem mediana de 20 h e o grupo com bot tem mediana de 14 h, ou seja, **existe efeito de verdade** nesse conjunto.

> Os números abaixo usam o `config/cenario.yaml` provisório. Quando o Arthur gerar o arquivo com os parâmetros reais, rodar de novo e atualizar a tabela.

## Resultado

| Teste | Estatística | p-valor | Tamanho do efeito | Rejeita H₀ (α = 0,05)? |
|---|---|---|---|---|
| t de Welch | t = 0,80 | 0,429 | d de Cohen = 0,21 (pequeno) | Não |
| Mann-Whitney | U = 552 | 0,134 | delta de Cliff = 0,23 (pequeno) | Não |

Medianas da amostra: 22,1 h (sem bot) e 16,6 h (com bot). Médias: 26,1 h e 22,0 h.

## O que cada teste concluiu e por quê

**Welch.** Compara as médias dos dois grupos. Com p = 0,43, não há evidência de diferença. O tempo de merge é muito assimétrico: poucos PRs que demoram muito puxam a média e aumentam bastante a variância. Isso deixa o erro padrão grande, a estatística t fica pequena (0,80) e o teste não consegue separar o efeito do ruído.

**Mann-Whitney.** Compara os postos, ou seja, se um PR do grupo sem bot tende a demorar mais que um do grupo com bot. Como usa a ordem e não o valor, os PRs muito demorados pesam igual aos outros. Por isso o p-valor caiu bastante (0,13), mas ainda ficou acima de 0,05.

**Conclusão.** Os dois testes não rejeitaram H₀, mas sabemos que o efeito existe, então os dois cometeram **erro tipo II** nesse conjunto. Com só 30 PRs por grupo e um efeito pequeno, isso é esperado. O Mann-Whitney chegou mais perto de detectar o efeito, o que é um primeiro sinal de que ele pode ter mais poder com dados assimétricos. Um único conjunto não prova isso: a S02 (10.000 repetições) é que vai mostrar se essa vantagem se confirma.
