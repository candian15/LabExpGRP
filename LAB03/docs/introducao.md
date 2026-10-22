# Introdução

> Seção escrita pelos três. As hipóteses ficam em `hipoteses_rq3_rq5.md`, que entra logo
> depois desta seção no artigo. A versão LaTeX está em `introducao.tex`.

As métricas DORA, propostas pelo programa *DevOps Research and Assessment*, descrevem o
desempenho de entrega de uma equipe de software por quatro indicadores: a frequência de
*deploy*, o *lead time* para mudanças, a taxa de falha das mudanças e o tempo de recuperação
após uma falha. Com os quatro, a equipe é classificada como *Elite*, *High*, *Medium* ou
*Low*, e a literatura associa as categorias superiores a
práticas como integração contínua, automação de testes e implantação em pequenos lotes.

Essas métricas foram estabelecidas a partir de questionários respondidos por profissionais, e
isso limita seu uso fora desse contexto. Os dados originais são autorrelatados e privados,
então ninguém consegue auditá-los nem reproduzi-los. Além disso, as faixas de desempenho foram calibradas em equipes corporativas que praticam
entrega contínua, e não se sabe o que elas significam quando aplicadas a projetos
*open-source*, cujo ritmo de publicação é decidido por mantenedores voluntários.

Neste trabalho calculamos as quatro métricas apenas com dados públicos do GitHub, sobre uma amostra de 350 repositórios populares que usam GitHub
Actions, em uma janela fixa de 12 meses. Como a API não informa quando uma mudança chegou à
produção nem quando um defeito afetou usuários, usamos dois *proxies*: a publicação
de uma *release* aproxima o *deploy*, e a falha de um *workflow* de integração contínua
aproxima a falha de uma mudança. Toda a coleta é reproduzida por um único comando, e o
conjunto de dados resultante é publicado junto com o código.

Como os valores dependem desses *proxies*, também os verificamos. Sorteamos uma
amostra-ouro de 60 repositórios e 299 *releases*, que os três autores julgaram de forma
independente; medimos a concordância entre eles e avaliamos contra esse consenso a
heurística automática que identifica *releases* corretivas. Por fim, comparamos três
definições alternativas de *deploy* para ver o quanto as conclusões mudam com elas, e a
discussão usa bastante esses resultados.

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
clássicas, e a Seção 6 apresenta as conclusões.
