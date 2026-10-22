# Resultados: RQ 05 e RQ 06

> Parte do Arthur na seção de Resultados. Os números vêm de `resultados/rq5_spearman.csv` e
> `resultados/rq6_testes.csv`, gerados por `analises.rq5_correlacao` e `analises.rq6_fatores`.
> A versão LaTeX está em `resultados_rq5_rq6.tex`.

## RQ 05: Frequência de deploy e taxa de falha se correlacionam?

Calculamos a correlação de Spearman entre a frequência de deploy e o CFR, separadamente para
cada variante. Spearman trabalha com postos, o que é adequado às distribuições assimétricas
observadas e ao grande número de empates em zero no CFR (a).

| Variante do CFR | n | ρ | p | Interpretação |
|---|---:|---:|---:|---|
| (a) proxy de CI | 350 | 0,127 | 0,017 | fraca positiva |
| (b) proxy de entrega | 350 | 0,613 | < 0,001 | forte positiva |

As duas são estatisticamente significativas ao nível de 5%, mas o coeficiente da variante (b)
é quase cinco vezes o da (a). Na variante (a), um ρ de 0,127 explica menos de 2% da variância conjunta:
na prática, frequência de publicação e falha de CI são independentes nesta amostra. Na
variante (b), o ρ de 0,613 indica associação forte.

A Figura 4 mostra as duas dispersões, com a frequência em escala logarítmica.

## RQ 06: Que fatores explicam as diferenças de desempenho?

Comparamos cada métrica entre subgrupos de cinco fatores: linguagem (as cinco mais frequentes,
e "Outras"), quartis de estrelas, quartis de contribuidores, quartis de idade e tipo do
projeto. Usamos Kruskal-Wallis para três ou mais grupos e Mann-Whitney para dois, com ε² e
Cliff's delta como tamanho de efeito. Como são 30 testes simultâneos, aplicamos a correção de
Holm sobre o conjunto.

Doze dos 30 testes permanecem significativos após a correção. A tabela abaixo traz apenas
esses, ordenados pelo tamanho de efeito.

| Fator | Métrica | p (Holm) | ε² |
|---|---|---:|---:|
| Idade | Lead time (a) | < 0,001 | 0,288 |
| Idade | Lead time (b) | < 0,001 | 0,251 |
| Contribuidores | Lead time (b) | < 0,001 | 0,171 |
| Idade | CFR (b) | < 0,001 | 0,164 |
| Idade | Frequência | < 0,001 | 0,106 |
| Contribuidores | Lead time (a) | < 0,001 | 0,104 |
| Linguagem | Lead time (a) | < 0,001 | 0,099 |
| Linguagem | Frequência | < 0,001 | 0,097 |
| Linguagem | CFR (b) | < 0,001 | 0,084 |
| Linguagem | Lead time (b) | 0,001 | 0,078 |
| Idade | Recuperação | 0,016 | 0,051 |
| Estrelas | Lead time (b) | 0,014 | 0,049 |

Por fator, a idade aparece em cinco métricas, a linguagem em quatro, os contribuidores em
duas e as estrelas em uma. Nenhum teste sobre o tipo do projeto sobreviveu à correção, e
esse fator só existe para os 60 repositórios da amostra-ouro, de modo que os testes sobre ele
têm poder reduzido.

Entre os testes significativos, ε² vai de 0,049 a 0,288; o maior corresponde à idade sobre
o lead time (a). Nenhum fator isolado explica a maior parte da variação observada.
