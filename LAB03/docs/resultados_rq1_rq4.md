# Resultados: RQ 01 a RQ 04

> Parte do João na seção de Resultados. Os números saem de
> `resultados/rq1_rq4_descritiva.csv`, `rq1_rq4_dora.csv` e `rq1_rq4_notas.csv`, gerados por
> `python -m analises.rq1_rq4_descritiva`. A versão LaTeX está em `resultados_rq1_rq4.tex`.
>
> Todos os números são definitivos, calculados sobre o dataset final, com a heurística v4
> do CFR (b).

## Visão geral

A amostra final tem 350 repositórios. Como as quatro métricas têm distribuições
assimétricas e cauda longa, reportamos mediana e intervalo interquartil (IQR), e não média
e desvio padrão. A Tabela~1 resume as seis variáveis.

| Métrica | n | Q1 | Mediana | Q3 | IQR |
|---|---|---|---|---|---|
| Frequência de deploy (releases/semana) | 350 | 0,19 | 0,42 | 1,04 | 0,84 |
| Lead time (a) (horas) | 350 | 50,8 | 251,7 | 848,4 | 797,6 |
| Lead time (b) (horas) | 350 | 65,4 | 284,0 | 845,4 | 780,1 |
| CFR (a), proxy de CI | 350 | 0,021 | 0,049 | 0,121 | 0,100 |
| CFR (b), proxy de entrega | 350 | 0,052 | 0,200 | 0,416 | 0,364 |
| Tempo de recuperação (horas) | 330 | 0,98 | 2,56 | 9,53 | 8,55 |

## RQ 01 — Com que frequência são feitos deploys?

A mediana é de **0,42 release por semana**, ou aproximadamente uma release a cada duas
semanas e meia, com IQR de 0,84. A distribuição é fortemente assimétrica à direita
(Figura~1): 260 repositórios (74,3%) publicam menos de uma release por semana, e apenas 5
(1,4%) alcançam o patamar *Elite* de sete ou mais releases semanais. O máximo observado é
de 49,6 releases por semana.

Pela classificação DORA, a frequência é a dimensão em que a amostra vai pior: 107
repositórios (30,6%) ficam em *Low* e 153 (43,7%) em *Medium*. Vale notar que os cortes
DORA foram concebidos para *deploys* em ambientes corporativos de entrega contínua,
enquanto uma *release* publicada no GitHub é um marco de versionamento, frequentemente
mensal ou trimestral por decisão do projeto. A frequência baixa, aqui, reflete a prática de
versionamento do ecossistema open-source e não necessariamente uma capacidade de entrega
limitada.

## RQ 02 — Qual o lead time para mudanças?

As duas variantes dão resultados próximos: **251,7 horas (10,5 dias)** na variante (a), que
mede da publicação da *release* até o *commit* mais antigo nela, e **284,0 horas (11,8
dias)** na variante (b), que considera todos os *commits* da *release*. Os IQRs também são
semelhantes (797,6 h e 780,1 h) e as caixas se sobrepõem quase inteiramente (Figura~2,
à esquerda). A correlação de Spearman entre elas é de **0,744**.

A proximidade é um resultado útil: a escolha entre as duas operacionalizações do *lead
time* altera pouco a conclusão, o que dá robustez à RQ 02. A dispersão, porém, é grande em
ambas — de 0,06 h a 1,1 × 10⁵ h na variante (a) —, o que separa projetos que publicam a
partir de um ramo de desenvolvimento recente daqueles que acumulam *commits* por meses
antes de publicar.

Na classificação, o *lead time* distribui os repositórios de forma relativamente equilibrada:
57 em *Elite*, 89 em *High*, 103 em *Medium* e 101 em *Low*.

## RQ 03 — Qual a taxa de falha das mudanças?

É a questão em que as duas variantes mais divergem, e em que as hipóteses da Introdução
falharam nas duas direções.

A variante (a), proxy de CI, tem mediana de **0,049** (4,9%), com IQR de 0,100. A hipótese
previa uma mediana entre 10% e 25%; o valor observado é menos da metade do piso previsto.
Treze repositórios (3,7%) não têm nenhum *run* com falha na janela. A explicação provável é
que os *runs* contados são disparados por *push* no *default branch*, ou seja, mudanças que
já passaram pela validação de um *pull request* antes do *merge*: o que se mede ali é a
taxa de falha do que já foi aprovado, e não a de todas as mudanças propostas.

A variante (b), proxy de entrega, tem mediana de **0,200** (20,0%), com IQR de 0,364. A
hipótese previa valores "parecidos ou menores" que os da variante (a) e uma concentração em
0%; o observado é quatro vezes maior que o da variante (a), embora 80 repositórios (22,9%)
de fato fiquem em zero.

A hipótese que se confirmou foi a terceira: **as duas variantes concordam pouco.** A
divergência vai além das medianas — a correlação de Spearman entre elas é de **0,107**
(p = 0,045), praticamente nula, o que significa que elas não apenas produzem valores diferentes, mas
ordenam os repositórios de maneiras diferentes. Um repositório bem avaliado por uma pode
ser mal avaliado pela outra. A Figura~2, à direita, mostra as duas distribuições lado a
lado.

Esse é o ponto de maior fragilidade de constructo do trabalho e é retomado na seção de
Ameaças à Validade. Pela variante (a), 283 repositórios (80,9%) ficam na faixa *Elite*
(CFR ≤ 0,15), o que torna essa a nota mais generosa das quatro e puxa a classificação geral
para cima.

## RQ 04 — Qual o tempo de recuperação de uma falha?

A mediana é de **2,56 horas**, com IQR de 8,55 h, calculada sobre os 330 repositórios que
tiveram ao menos um episódio de falha seguida de sucesso na janela. A hipótese da Introdução
se confirma: previa-se "algumas horas" e a maioria na faixa *High* (de 1 hora a menos de um
dia), e de fato 196 repositórios (59,4%) caem nessa faixa, contra 86 (26,1%) em *Elite*
(menos de 1 hora) e 48 (14,5%) em 24 horas ou mais. A cauda longa também se confirma: o
máximo observado é de 1.418 horas, quase dois meses.

**Vinte repositórios (5,7%) não tiveram nenhum episódio na janela** e ficam fora do cálculo
da mediana, como determina o protocolo. Eles estão listados em
`resultados/rq1_rq4_sem_recuperacao.csv`. São, em sua maioria, repositórios cujos *workflows*
não registraram falha alguma no período — e não repositórios inativos: `arendst/Tasmota`, por
exemplo, tem 569 *runs* válidos e nenhuma falha.

Uma hipótese **não** se confirmou: esperava-se "uma proporção não trivial de episódios
censurados", isto é, episódios que a janela de observação não viu encerrar. A censura foi
desprezível: a mediana da proporção de episódios censurados é 0, o terceiro quartil é
0,0033, e 234 dos 330 repositórios (70,9%) não têm nenhum episódio censurado. Na prática,
quase toda falha iniciada dentro da janela também foi resolvida dentro dela, o que reforça a
confiança na mediana reportada.

## Classificação DORA geral

A categoria de cada repositório é a mediana das quatro notas, arredondada para baixo.

| Categoria | n | % |
|---|---|---|
| Elite | 25 | 7,1 |
| High | 143 | 40,9 |
| Medium | 159 | 45,4 |
| Low | 23 | 6,6 |

A amostra se concentra no meio da escala: 302 repositórios (86,3%) são *High* ou *Medium*, e
as duas pontas somam menos de 14%. A distribuição por nota (`rq1_rq4_notas.csv`) mostra que
esse resultado é puxado para cima pela nota de CFR, *Elite* em 80,9% dos casos, e para baixo
pela nota de frequência, *Low* ou *Medium* em 74,3%. O perfil típico da amostra é, portanto,
o de projetos que publicam com pouca frequência, mas com baixa taxa de falha de CI e
recuperação rápida.

Como a nota de CFR usa a variante (a), e como essa variante diverge fortemente da (b)
(RQ 03), essa distribuição depende da definição operacional adotada. O efeito é quantificado
na seção de Ameaças à Validade.
