# Discussão e Ameaças à Validade

> Seções escritas pelos três. Os números vêm de `resultados/`, `validacao/kappa.csv` e
> `dados/funil.csv`. A versão condensada, usada no artigo, está em `discussao_ameacas.tex`.
>
> Todos os números são definitivos, calculados sobre o dataset final, com a heurística v4
> do CFR (b).

## Discussão

### Hipóteses e resultados

| RQ | Hipótese | Observado | Situação |
|---|---|---|---|
| 01 | Mediana entre 1/mês e 1/semana; maioria abaixo de 1/semana | 0,42/semana; 74,3% abaixo de 1/semana | Confirmada |
| 02 | Mediana de semanas; (a) maior que (b) | 10,5 dias; (a) maior em 62% dos repositórios, mas não na mediana | Parcial |
| 03 | CFR (a) de 10% a 25%; (b) igual ou menor; pouca concordância | 4,9%; 20,0%; ρ = 0,107 | Parcial |
| 04 | Horas, maioria *High*, cauda longa, censura não trivial | 2,56 h; 59,4% *High*; até 1.418 h; censura desprezível | Parcial |
| 05 | (a) fraca negativa ou nula; (b) positiva | (a) fraca e positiva, 0,127; (b) 0,613 | Parcial |
| 06 | Estrelas e contribuidores melhoram; idade reduz a frequência; linguagem pesa pouco | Idade é o fator mais forte; estrelas quase sem efeito; mais contribuidores, *lead time* maior | Parcial |
| 07 | Menos de 20% mudam; tags aumentam os *Elite* | 25% a 33% mudam; *Elite* de 25 para 33 | Parcial |
| 08 | Maior que o CFR (b), cerca de um terço | 0,500 contra 0,200 | Parcial |

Das oito hipóteses, só a da RQ 01 se confirmou por inteiro. As que mais erraram foram as de
taxa de falha e a da RQ 07, que esperava uma classificação estável entre as definições de
*deploy*. Na RQ 02, a variante (a) é maior que a (b) na maioria dos repositórios, como
esperado, mas a mediana da amostra se inverte, provavelmente porque a (b) dá mais peso às
releases grandes, que acumulam *commits* antigos. Na RQ 06, o efeito dos contribuidores foi o
oposto do esperado: os repositórios com mais contribuidores têm *lead time* maior (mediana de
628 h no quartil superior, contra 67 h no inferior, na variante (b)).

### As hipóteses sobre a taxa de falha erraram nas duas direções

A Introdução previa que o CFR na variante (a) ficaria entre 10% e 25%. O valor observado foi
de 4,9%, menos da metade do piso previsto. A explicação está na própria definição
operacional: os *runs* contabilizados são disparados por *push* no *default branch*, ou seja,
mudanças que já passaram pela revisão de um *pull request* antes do *merge*. O que a métrica
captura é a taxa de falha do que já foi aprovado, e não a de todas as mudanças propostas. Em
projetos open-source populares, com revisão obrigatória e CI rodando sobre o PR, essa taxa é
naturalmente baixa.

Para a variante (b) a previsão era de valores "parecidos ou menores" e uma concentração em
0%. O observado foi o oposto: mediana de 0,200, quatro vezes maior que a da variante
(a), ainda que 80 repositórios (22,9%) de fato fiquem em zero. Parte da diferença vem do
instrumento: a heurística que decide o que é uma *release* corretiva não atinge o F1 mínimo
de 0,70 exigido, alcançando 0,65 na versão adotada. A direção do erro, porém, é conhecida:
a heurística ainda produz mais falsos positivos (57) do que falsos negativos (30), de modo
que 0,200 tende a superestimar o valor real.

A única hipótese que se confirmou sobre a RQ 03 foi a de que as duas variantes concordariam
pouco, e ela se confirmou de forma mais forte do que o previsto.

### As duas variantes do CFR medem coisas diferentes

O trabalho mediu duas vezes a mesma métrica DORA, *change failure rate*, com dois *proxies*
distintos. Além da diferença de magnitude, a correlação de Spearman entre as variantes é de
0,107 (p = 0,045), praticamente nula: elas não ordenam os repositórios da mesma forma, e um
projeto bem avaliado por uma pode ser mal avaliado pela outra.

O efeito sobre a conclusão do trabalho é direto. A classificação DORA geral usa a nota do
CFR (a). Recalculando-a com a variante (b), 72 dos 350 repositórios (20,6%) mudam de
categoria, e a faixa *Elite* cai de 25 para 8 repositórios. A distribuição principal (7,1%
*Elite* e 40,9% *High*) depende, portanto, da definição operacional escolhida, e não só dos
repositórios estudados.

Na RQ 02 foi diferente: as duas variantes do *lead time* produziram
medianas próximas (251,7 h e 284,0 h) e correlação de 0,744. A escolha entre
operacionalizações importa pouco para o *lead time* e muito para o CFR. A diferença é que as
duas variantes do *lead time* medem o mesmo evento por janelas diferentes, enquanto as duas
variantes do CFR medem eventos distintos: falha de *pipeline* antes da entrega, de um lado, e
necessidade de correção depois da entrega, do outro.

### A escala DORA não foi desenhada para releases de projetos open-source

A frequência de deploy é a dimensão em que a amostra vai pior: 74,3% dos repositórios
publicam menos de uma *release* por semana, e apenas 5 dos 350 alcançam o patamar *Elite*.

Esse resultado reflete mais a distância entre o conceito e o *proxy* do que a capacidade
de entrega desses projetos. Uma *release* publicada no GitHub é um marco de
versionamento, decidido pelos mantenedores e frequentemente mensal ou trimestral. Um *deploy*,
no sentido do DORA, é a colocação de uma mudança em produção, que em muitos desses projetos
acontece continuamente e sem gerar *release* alguma. A faixa *Elite* da frequência, de sete
*deploys* por semana, pressupõe entrega contínua em ambiente corporativo; aplicá-la a marcos
de versionamento classifica como lentos projetos que apenas versionam com parcimônia.

### A classificação geral é dominada por uma única nota

A categoria final de cada repositório é a mediana das quatro notas. A distribuição das notas
isoladas mostra que elas não contribuem igualmente: a nota de CFR é *Elite* em 80,9% dos
casos, porque o corte *Elite* (CFR ≤ 0,15) é generoso diante de uma mediana observada de
0,049. A nota de frequência, no sentido oposto, é *Low* ou *Medium* em 74,3%.

O perfil típico da amostra é o de projetos que publicam com pouca frequência, mas com baixa
taxa de falha de CI e recuperação rápida (mediana de 2,56 h, com 59,4% na faixa *High*). Como
a mediana de quatro notas é pouco sensível a uma única delas, a classificação geral acaba
determinada pelo par CFR/recuperação, as duas dimensões em que a amostra vai melhor.

### Velocidade e estabilidade (RQ 05)

A hipótese previa correlação fraca negativa ou nula entre frequência de *deploy* e CFR na
variante (a), e positiva na variante (b). As duas previsões se confirmaram na direção, e a
segunda com força muito maior que a esperada.

Na variante (a), a correlação de Spearman é de ρ = 0,127 (p = 0,017, n = 350): positiva,
mas fraca a ponto de não ter relevância prática. Não há evidência de que
publicar com mais frequência venha acompanhado de mais falhas de CI, o que é compatível com a
tese do DORA de que velocidade e estabilidade não constituem um *trade-off*.

Na variante (b), a correlação é de ρ = 0,613 (p < 0,001): forte e positiva. Tomada ao pé
da letra, ela diria que os projetos que publicam mais falham muito mais. A hipótese já
antecipava que esse resultado seria, em boa medida, um artefato da própria métrica, e a
explicação se sustenta: o CFR (b) marca uma *release* como falha quando a *release* seguinte,
publicada em até 7 dias, é corretiva. Quem publica semanalmente tem muito mais oportunidades
de satisfazer essa condição do que quem publica trimestralmente, independentemente da
qualidade do que entrega.

Por isso reportamos as duas variantes em separado. Com apenas a (b), a conclusão seria o
oposto do que o DORA sustenta, e por causa da construção da métrica, não do comportamento
dos projetos.

### O que explica as diferenças entre projetos (RQ 06)

Dos 30 testes de Kruskal-Wallis, 12 permanecem significativos após a correção de Holm. Os
tamanhos de efeito desses 12, medidos por ε², vão de 0,049 a 0,288.

A idade do repositório é o fator mais forte, e aparece em cinco das seis métricas. O efeito
mais pronunciado é sobre o *lead time* (ε² = 0,288 na variante (a) e 0,251 na (b)): projetos
mais antigos acumulam mais tempo entre o *commit* mais antigo e a publicação. A idade também
se associa ao CFR (b) (ε² = 0,164), à frequência de *deploy* (ε² = 0,106) e, com efeito
menor, ao tempo de recuperação (ε² = 0,051).

O número de contribuidores se associa às duas variantes do *lead time* (ε² = 0,171 na (b) e
0,104 na (a)), e a linguagem aparece em quatro métricas, com ε² entre 0,078 e 0,099. A
popularidade, medida por quartis de estrelas, só sobrevive à correção em uma métrica, o
*lead time* (b), com o menor efeito de todos (ε² = 0,049): o número de estrelas quase não
explica o desempenho de entrega.

Nenhum teste sobre o tipo do projeto foi significativo. Esse fator, porém, só existe para
os 60 repositórios da amostra-ouro, e os testes sobre ele têm poder reduzido: a ausência de
significância ali não deve ser lida como ausência de efeito.

### A definição de deploy muda a conclusão? (RQ 07 e RQ 08)

Entre um quarto e um terço dos repositórios trocam de categoria conforme a definição de
*deploy* adotada (tabela da RQ 07 nos Resultados), e a concordância entre as classificações é
apenas moderada. A faixa *Elite* é a mais instável: 25 repositórios em C1, 8 em C2 e 33 em
C3, uma variação de quatro vezes entre os extremos sobre o mesmo conjunto de projetos e a
mesma janela.

A RQ 08 ajuda a ler o CFR (b). O *rework rate* conta toda *release* corretiva e tem mediana
de 0,500; o CFR (b), que só conta correções em até 7 dias, fica em 0,200. Ou seja, a maior
parte das correções nesses projetos é manutenção de rotina, e o CFR (b) captura só a fração
que responde a uma entrega recente.

### As conclusões são robustas?

Depende da RQ. A do *lead time* (RQ 02) se mantém nas duas variantes. As da taxa de falha
(RQ 03 e 05) e a classificação geral não se mantêm: trocar a variante do CFR muda a categoria
de 20,6% dos repositórios, e trocar a unidade de *deploy* muda entre 25% e 33%, e nenhum desses
ICs desce abaixo de 21%.

## Ameaças à Validade

Seguimos as quatro categorias de Wohlin et al.

### Validade de construto

As ameaças mais sérias do trabalho estão nesta categoria.

*Release não é deploy.* Muitos projetos entregam continuamente sem publicar *release*, e outros publicam
*releases* que são apenas marcos de versionamento, sem qualquer implantação associada. A
validação manual mediu diretamente esse risco: os três avaliadores julgaram, para cada
repositório da amostra-ouro, se as *releases* representam entregas reais ao usuário, e o
consenso foi afirmativo em 59 dos 60 casos. É um indício favorável, mas limitado a uma
amostra de 60 repositórios populares.

*Falha de CI não é falha em produção.* Um *workflow run* que falha é, na maior parte das
vezes, um erro capturado antes de chegar ao usuário, que é a finalidade do CI.
Contá-lo como *change failure* inverte o sentido da métrica DORA, que mede falhas que
atingiram produção. Essa é a explicação mais provável para o CFR (a) observado (4,9%) ter
ficado abaixo do previsto.

*As duas variantes do CFR não medem a mesma coisa.* A correlação entre elas é de 0,107 e
20,6% dos repositórios mudam de categoria conforme a variante adotada. Qualquer afirmação
sobre a taxa de falha da amostra é condicional à variante escolhida.

*A heurística de release corretiva não atinge o limiar exigido.* As versões testadas ficaram
entre 0,56 e 0,65 de F1, abaixo do mínimo de 0,70. A versão adotada, a v4, alcançou 0,65.
O CFR (b), a RQ 08 e o C2 da RQ 07
herdam esse erro de medida. Mesmo os avaliadores não foram unânimes nessa dimensão: o kappa de Fleiss para *release* corretiva foi de 0,876, com 26
divergências em 299 itens. Esse valor funciona como teto prático para qualquer heurística
automática avaliada contra esse consenso.

*O `commit.author.date` é distorcido por rebase e squash merge.* Essas operações reescrevem a
data do commit, o que afeta diretamente as duas variantes do *lead time*. Não há como
detectá-las pela API, e o efeito é de direção desconhecida.

### Validade interna

As análises são observacionais e correlacionais; nenhuma afirmação causal é feita.

Medimos as associações entre os metadados e as métricas e encontramos relações não
desprezíveis: a idade do repositório correlaciona-se negativamente com a frequência de deploy
(ρ = −0,306, p < 0,001), e o número de estrelas (ρ = 0,162) e de contribuidores (ρ = 0,119)
positivamente. Projetos mais antigos publicam menos *releases* na janela, e projetos mais
populares publicam mais. Esses fatores não foram controlados nas RQ 01 a RQ 04, que são
descritivas; a RQ 06 os trata explicitamente como fatores.

O filtro de inclusão introduz seleção: só entraram repositórios com pelo menos 5
*releases* e 50 *runs* válidos na janela. Dos 1.057 candidatos que usam Actions, 618 foram
descartados por publicar menos de 5 *releases* e 81 por ter menos de 50 *runs*. A amostra
final é, por construção, composta de projetos que já versionam e já automatizam com
regularidade, o que restringe a variação na dimensão da RQ 01.

Seis repositórios foram descartados por ultrapassarem 1.000 *runs* em um único dia, limite
acima do qual a API não devolve o conjunto completo. Preferimos excluí-los a calcular métricas
sobre um subconjunto truncado de tamanho desconhecido, mas isso remove da amostra
os projetos de maior atividade de CI. Outros dois saíram por erro definitivo da API.

### Validade externa

A limitação mais importante é que a amostra não é aleatória. A busca do GitHub devolve no
máximo 1.000 resultados por consulta, e cada faixa de estrelas do `config.yaml` contém muito
mais repositórios que isso (a faixa de 1.000 a 1.500 estrelas sozinha tem mais de 20 mil).
Entraram, portanto, os 1.000 mais estrelados de cada uma das sete faixas, e não um sorteio
delas. Fatiar a busca em faixas estreitas atenua
o viés, mas não o elimina: dentro de qualquer faixa com mais de 1.000 repositórios, os menos
estrelados nunca são observados.

A amostra deve ser lida como "repositórios populares que usam GitHub Actions", e não como
"repositórios com mais de 1.000 estrelas". Projetos privados e corporativos estão
fora, e são o contexto para o qual as faixas DORA foram concebidas. Nenhuma
conclusão aqui se transfere automaticamente para equipes corporativas de entrega contínua.

A janela de observação é única e fixa, de 12 meses. Não há como separar o que é
característica estável de um projeto do que é efeito do período: um projeto pode ter passado
por uma migração de CI, uma reescrita ou uma troca de mantenedores dentro da janela.

### Validade de conclusão

Usamos mediana e IQR em vez de média e desvio padrão,
porque todas as distribuições são assimétricas com cauda longa; a média seria dominada pelos
extremos. Nas correlações usamos Spearman, que trabalha com postos e não pressupõe
normalidade nem linearidade, o que é adequado para distribuições como as observadas. O grande
número de empates em zero no CFR (a) é tratado pela média dos postos.

Nos testes por subgrupo da RQ 06 são feitas 30 comparações simultâneas, o que inflaria o erro
tipo I; aplicamos a correção de Holm, mais conservadora que o nível nominal de 5%. Os
tamanhos de efeito são reportados junto dos p-valores (ε² e Cliff's delta), porque
significância estatística com n = 350 não implica relevância prática.

Alguns subgrupos são pequenos. O tipo do projeto, usado como fator na RQ 06, só existe para
os 60 repositórios da amostra-ouro, e os testes sobre ele têm poder reduzido: um resultado não
significativo ali não deve ser lido como ausência de efeito.

O tempo de recuperação é calculado sobre 330 repositórios; os 20 sem episódio na janela são
reportados à parte, e não imputados. A censura dentro da janela mostrou-se desprezível (70,9%
dos repositórios não têm nenhum episódio censurado), o que reduz o risco de subestimação da
mediana.

Os ICs por *bootstrap* mostram que as medianas e as proporções de mudança de categoria são
estáveis, mas que a correlação entre as variantes do CFR (0,107, IC de −0,0001 a 0,21) não se
distingue com segurança de zero.

Por fim, o kappa de "releases são entregas reais" (0,745) deve ser lido junto com a
distribuição dos rótulos: como o consenso pôs 59 dos 60 repositórios na mesma categoria, uma
única divergência basta para derrubar o coeficiente, embora a concordância bruta seja de
98,3%.
