# Introdução

> Seção escrita pelos três. As hipóteses ficam em `hipoteses_rq3_rq5.md`, que entra logo
> depois desta seção no artigo. A versão LaTeX está em `introducao.tex`.

As métricas DORA, propostas pelo programa *DevOps Research and Assessment*, descrevem o
desempenho de entrega de uma equipe de software por quatro indicadores: a frequência de
*deploy*, o *lead time* para mudanças, a taxa de falha das mudanças e o tempo de recuperação
após uma falha. A combinação dos quatro posiciona a equipe em uma de quatro categorias —
*Elite*, *High*, *Medium* ou *Low* — e a literatura associa as categorias superiores a
práticas como integração contínua, automação de testes e implantação em pequenos lotes.

Essas métricas foram estabelecidas a partir de questionários respondidos por profissionais,
o que traz duas limitações para quem quer aplicá-las fora desse contexto. A primeira é que os
dados originais são autorrelatados e privados: não há como auditá-los nem reproduzi-los. A
segunda é que as faixas de desempenho foram calibradas em equipes corporativas que praticam
entrega contínua, e não se sabe o que elas significam quando aplicadas a projetos
*open-source*, cujo ritmo de publicação é decidido por mantenedores voluntários.

Este trabalho investiga o que acontece quando as quatro métricas são calculadas **apenas com
dados públicos do GitHub**, sobre uma amostra de 350 repositórios populares que usam GitHub
Actions, em uma janela fixa de 12 meses. Como a API não informa quando uma mudança chegou à
produção nem quando um defeito afetou usuários, dois *proxies* são necessários: a publicação
de uma *release* aproxima o *deploy*, e a falha de um *workflow* de integração contínua
aproxima a falha de uma mudança. Toda a coleta é reproduzida por um único comando, e o
conjunto de dados resultante é publicado junto com o código.

Medir por *proxy* exige verificar o *proxy*. Por isso o estudo não se limita a reportar os
valores: ele sorteia uma amostra-ouro de 60 repositórios e 299 *releases*, submete-a ao
julgamento independente dos três autores, mede a concordância entre eles e avalia contra esse
consenso a heurística automática que identifica *releases* corretivas. A sensibilidade das
conclusões à definição de *deploy* também é testada, comparando três operacionalizações
alternativas. O resultado dessas verificações é tão relevante quanto os valores das métricas,
e sustenta boa parte da discussão.

## Questões de pesquisa

| RQ | Pergunta |
|---|---|
| RQ 01 | Com que frequência são feitos *deploys* nesses projetos? |
| RQ 02 | Qual o *lead time* para mudanças, nas variantes (a) e (b)? |
| RQ 03 | Qual a taxa de falha das mudanças, nas variantes (a) e (b)? |
| RQ 04 | Qual o tempo de recuperação após uma falha? |
| RQ 05 | Frequência de *deploy* e taxa de falha se correlacionam? |
| RQ 06 | Linguagem, popularidade, número de contribuidores, idade e tipo do projeto explicam diferenças no desempenho? |
| RQ 07 | A classificação muda se a unidade de *deploy* for definida de outra forma? |
| RQ 08 | Qual a proporção de *releases* corretivas (*rework rate*) e como ela se compara ao CFR (b)? |

Nas RQ 01 a RQ 04 reportamos a mediana e o intervalo interquartil de cada métrica, além da
distribuição das categorias DORA.

## Estrutura do artigo

A Seção 2 descreve a metodologia: a fonte de dados e a seleção da amostra, as definições
operacionais de cada métrica e a heurística do CFR (b), e o protocolo da validação manual. A
Seção 3 apresenta os resultados por questão de pesquisa. A Seção 4 discute o que as hipóteses
previam e o que foi observado. A Seção 5 reúne as ameaças à validade nas quatro categorias
clássicas, e a Seção 6 relata a replicação cruzada do pipeline de outro grupo.
