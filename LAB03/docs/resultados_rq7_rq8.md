# Resultados: RQ 07 e RQ 08

> Parte do Pedro na seção de Resultados. Os números vêm de `resultados/rq7_*.csv` e
> `resultados/rq8_*.csv`, gerados por `analises.rq7_sensibilidade` e `analises.rq8_rework`.
> A versão LaTeX está em `resultados_rq7_rq8.tex`.

## RQ 07: A classificação muda se a unidade de deploy for outra?

Recalculamos a classificação DORA dos 350 repositórios sob três operacionalizações de
deploy:

| Combinação | Unidade de deploy | Lead time | CFR |
|---|---|---|---|
| C1 (referência) | release | (a) | (a) |
| C2 | release + pré-release | (b) | (b) |
| C3 | tag | (b) | (a) |

A distribuição das categorias muda de forma substantiva entre elas:

| Categoria | C1 | C2 | C3 |
|---|---:|---:|---:|
| Elite | 25 | 8 | 33 |
| High | 143 | 134 | 164 |
| Medium | 159 | 186 | 138 |
| Low | 23 | 22 | 15 |

A concordância entre as classificações, medida pelo kappa ponderado, fica na faixa moderada:

| Par | Repositórios que mudam de categoria | Kappa ponderado |
|---|---:|---:|
| C1 × C2 | 32,9% | 0,515 |
| C1 × C3 | 25,4% | 0,657 |
| C2 × C3 | 28,0% | 0,602 |

Entre um quarto e um terço dos repositórios trocam de categoria conforme a definição. A faixa
*Elite* é a mais sensível: vai de 8 repositórios em C2 a 33 em C3, uma variação de quatro
vezes sobre o mesmo conjunto de projetos e a mesma janela de observação.

## RQ 08: Rework rate

O *rework rate* é a proporção de releases corretivas publicadas na janela, calculada como
`cfrb_releases_corretivas ÷ n_releases`. Diferente do CFR (b), ele conta toda release
corretiva, e não apenas as que vieram em até 7 dias depois de outra.

| Métrica | n | Q1 | Mediana | Q3 |
|---|---:|---:|---:|---:|
| Rework rate | 350 | 0,225 | 0,500 | 0,726 |
| CFR (b) | 350 | 0,052 | 0,200 | 0,416 |

A mediana do rework rate é 2,5 vezes a do CFR (b). As duas medidas se correlacionam
(ρ = 0,522, p < 0,001), mas 309 dos 350 repositórios têm rework rate maior que o CFR (b),
e 21 não publicaram nenhuma release corretiva na janela.

Metade das releases desses projetos corrige alguma coisa, mas apenas uma em cada cinco
corrige algo publicado na semana anterior. A maior parte do retrabalho é manutenção de
rotina, e não resposta a uma entrega recém-quebrada. Ao exigir a janela de 7 dias, o CFR (b)
mede um fenômeno mais estreito que "release corretiva".
