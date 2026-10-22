# Discussão e Ameaças à Validade

> Seções escritas pelos três. Os números vêm de `resultados/`, `validacao/kappa.csv` e
> `dados/funil.csv`. A versão LaTeX está em `discussao_ameacas.tex`.
>
> Os trechos entre `[[ ]]` dependem de resultados que ainda não foram gerados: o CFR (b) com
> a heurística final, e as RQ 05 a RQ 08.

## Discussão

### As hipóteses sobre a taxa de falha erraram nas duas direções

A Introdução previa que o CFR na variante (a) ficaria entre 10% e 25%. O valor observado foi
de **4,9%**, menos da metade do piso previsto. A explicação está na própria definição
operacional: os *runs* contabilizados são disparados por *push* no *default branch*, ou seja,
mudanças que já passaram pela revisão de um *pull request* antes do *merge*. O que a métrica
captura é a taxa de falha do que já foi aprovado, e não a de todas as mudanças propostas. Em
projetos open-source populares, com revisão obrigatória e CI rodando sobre o PR, essa taxa é
naturalmente baixa.

Para a variante (b) a previsão era de valores "parecidos ou menores" e uma concentração em
0%. O observado foi o oposto: mediana de **[[0,389]]**, quase oito vezes maior, com apenas
[[48]] repositórios em zero. Aqui a causa provável não é o fenômeno, e sim o instrumento: a
heurística que decide o que é uma *release* corretiva ainda não atinge o F1 mínimo de 0,70
exigido, e a versão em uso classifica como corretiva qualquer mudança de *patch* no SemVer.
Projetos que publicam *patches* com frequência — a prática recomendada em SemVer — são
penalizados por ela.

A única hipótese que se confirmou sobre a RQ 03 foi a de que as duas variantes concordariam
pouco. Ela se confirmou de forma mais forte do que o previsto, e é o resultado central desta
discussão.

### Duas operacionalizações do mesmo conceito, dois conceitos diferentes

O trabalho mediu duas vezes a mesma métrica DORA, *change failure rate*, com dois *proxies*
distintos. Os resultados não apenas diferem em magnitude: a correlação de Spearman entre as
duas variantes é de **[[0,093]]**, praticamente nula. Elas não ordenam os repositórios da
mesma forma, de modo que um projeto bem avaliado por uma pode ser mal avaliado pela outra.

O efeito sobre a conclusão do trabalho é direto. A classificação DORA geral usa a nota do
CFR (a). Recalculando-a com a variante (b), **[[114]] dos 350 repositórios ([[32,6%]]) mudam
de categoria**, e a faixa *Elite* cai de 25 para [[4]] repositórios. O resultado principal —
7,1% *Elite* e 40,9% *High* — não é, portanto, uma propriedade dos repositórios estudados,
mas uma consequência da definição operacional escolhida.

O contraste com a RQ 02 é instrutivo. Ali, as duas variantes do *lead time* produziram
medianas próximas (251,7 h e 284,0 h) e correlação de **0,744**. A escolha entre
operacionalizações importa pouco para o *lead time* e muito para o CFR. A diferença é que as
duas variantes do *lead time* medem o mesmo evento por janelas diferentes, enquanto as duas
variantes do CFR medem eventos distintos: falha de *pipeline* antes da entrega, de um lado, e
necessidade de correção depois da entrega, do outro.

### A escala DORA não foi desenhada para releases de projetos open-source

A frequência de deploy é a dimensão em que a amostra vai pior: 74,3% dos repositórios
publicam menos de uma *release* por semana, e apenas 5 dos 350 alcançam o patamar *Elite*.

Esse resultado diz menos sobre a capacidade de entrega desses projetos do que sobre a
distância entre o conceito e o *proxy*. Uma *release* publicada no GitHub é um marco de
versionamento, decidido pelos mantenedores e frequentemente mensal ou trimestral. Um *deploy*,
no sentido do DORA, é a colocação de uma mudança em produção, que em muitos desses projetos
acontece continuamente e sem gerar *release* alguma. A faixa *Elite* da frequência, de sete
*deploys* por semana, pressupõe entrega contínua em ambiente corporativo; aplicá-la a marcos
de versionamento classifica como lentos projetos que simplesmente versionam com parcimônia.

### A classificação geral é dominada por uma única nota

A categoria final de cada repositório é a mediana das quatro notas. A distribuição das notas
isoladas mostra que elas não contribuem igualmente: a nota de CFR é *Elite* em **80,9%** dos
casos, porque o corte *Elite* (CFR ≤ 0,15) é generoso diante de uma mediana observada de
0,049. A nota de frequência, no sentido oposto, é *Low* ou *Medium* em 74,3%.

O perfil típico da amostra é o de projetos que publicam com pouca frequência, mas com baixa
taxa de falha de CI e recuperação rápida — mediana de 2,56 h, com 59,4% na faixa *High*. Como
a mediana de quatro notas é pouco sensível a uma única delas, a classificação geral acaba
determinada pelo par CFR/recuperação, as duas dimensões em que a amostra vai melhor.

### [[Velocidade e estabilidade (RQ 05)]]

[[Depende do resultado da RQ 05: a correlação de Spearman entre frequência de deploy e CFR
nas duas variantes. A hipótese previa correlação fraca negativa ou nula na variante (a), em
linha com a tese do DORA de que velocidade e estabilidade não são um trade-off, e correlação
positiva na variante (b), por artefato da métrica — quem publica muitas releases tem mais
chance de publicar um patch em até 7 dias após qualquer release.]]

### [[O que explica as diferenças entre projetos (RQ 06)]]

[[Depende dos testes de Kruskal-Wallis com correção de Holm sobre linguagem, quartis de
estrelas, contribuidores, idade e tipo do projeto.]]

### [[A definição de deploy muda a conclusão? (RQ 07 e RQ 08)]]

[[Depende da análise de sensibilidade entre as combinações C1, C2 e C3 e do rework rate.]]

## Ameaças à Validade

Seguimos as quatro categorias de Wohlin et al.

### Validade de construto

**Estamos medindo o que achamos que medimos?** Esta é a ameaça mais séria do trabalho, e ela
tem três camadas.

*Release não é deploy.* O enunciado define a publicação de uma *release* como *proxy* de
*deploy*. Muitos projetos entregam continuamente sem publicar *release*, e outros publicam
*releases* que são apenas marcos de versionamento, sem qualquer implantação associada. A
validação manual mediu diretamente esse risco: os três avaliadores julgaram, para cada
repositório da amostra-ouro, se as *releases* representam entregas reais ao usuário, e o
consenso foi afirmativo em 59 dos 60 casos. É um indício favorável, mas limitado a uma
amostra de 60 repositórios populares.

*Falha de CI não é falha em produção.* Um *workflow run* que falha é, na maior parte das
vezes, um erro capturado **antes** de chegar ao usuário — que é a própria finalidade do CI.
Contá-lo como *change failure* inverte o sentido da métrica DORA, que mede falhas que
atingiram produção. Essa é a explicação mais provável para o CFR (a) observado (4,9%) ter
ficado abaixo do previsto.

*As duas variantes do CFR não medem a mesma coisa.* Como discutido acima, a correlação entre
elas é de [[0,093]] e [[32,6%]] dos repositórios mudam de categoria conforme a variante
adotada. Qualquer afirmação sobre a taxa de falha da amostra é condicional à variante
escolhida, e assim deve ser lida.

*A heurística de release corretiva não atinge o limiar exigido.* As versões testadas ficaram
entre [[0,56]] e [[0,64]] de F1, abaixo do mínimo de 0,70. O CFR (b), a RQ 08 e o C2 da RQ 07
herdam esse erro de medida. Vale registrar que mesmo os avaliadores humanos não foram
unânimes nessa dimensão: o kappa de Fleiss para *release* corretiva foi de 0,876, com 26
divergências em 299 itens. Esse valor funciona como teto prático para qualquer heurística
automática avaliada contra esse consenso.

*O `commit.author.date` é distorcido por rebase e squash merge.* Essas operações reescrevem a
data do commit, o que afeta diretamente as duas variantes do *lead time*. Não há como
detectá-las pela API, e o efeito é de direção desconhecida.

### Validade interna

**Há fatores não controlados que explicam os resultados?** As análises são observacionais e
correlacionais; nenhuma afirmação causal é feita.

Medimos as associações entre os metadados e as métricas e encontramos relações não
desprezíveis: a idade do repositório correlaciona-se negativamente com a frequência de deploy
(ρ = −0,306, p < 0,001), e o número de estrelas (ρ = 0,162) e de contribuidores (ρ = 0,119)
positivamente. Projetos mais antigos publicam menos *releases* na janela, e projetos mais
populares publicam mais. Esses fatores não foram controlados nas RQ 01 a RQ 04, que são
descritivas; a RQ 06 os trata explicitamente como fatores.

O **filtro de inclusão** introduz seleção: só entraram repositórios com pelo menos 5
*releases* e 50 *runs* válidos na janela. Dos 1.057 candidatos que usam Actions, 618 foram
descartados por publicar menos de 5 *releases* e 81 por ter menos de 50 *runs*. A amostra
final é, por construção, composta de projetos que já versionam e já automatizam com
regularidade — o que restringe a variação justamente na dimensão da RQ 01.

Seis repositórios foram descartados por ultrapassarem 1.000 *runs* em um único dia, limite
acima do qual a API não devolve o conjunto completo. Preferimos excluí-los a calcular métricas
sobre um subconjunto truncado de tamanho desconhecido, mas isso remove da amostra justamente
os projetos de maior atividade de CI. Outros dois saíram por erro definitivo da API.

### Validade externa

**Os resultados valem além da amostra?** A limitação mais importante é que **a amostra não é
aleatória**. A busca do GitHub devolve no máximo 1.000 resultados por consulta, e cada faixa
de estrelas do `config.yaml` contém muito mais repositórios que isso — a faixa de 1.000 a
1.500 estrelas sozinha tem mais de 20 mil. Entraram, portanto, os **1.000 mais estrelados de
cada uma das sete faixas**, e não um sorteio delas. Fatiar a busca em faixas estreitas atenua
o viés, mas não o elimina: dentro de qualquer faixa com mais de 1.000 repositórios, os menos
estrelados nunca são observados.

A amostra deve ser lida como "repositórios populares que usam GitHub Actions", e não como
"repositórios com mais de 1.000 estrelas". Projetos pequenos, privados ou corporativos estão
fora, e são justamente o contexto para o qual as faixas DORA foram concebidas. Nenhuma
conclusão aqui se transfere automaticamente para equipes corporativas de entrega contínua.

A janela de observação é **única e fixa**, de 12 meses. Não há como separar o que é
característica estável de um projeto do que é efeito do período — um projeto pode ter passado
por uma migração de CI, uma reescrita ou uma troca de mantenedores dentro da janela.

### Validade de conclusão

**A análise estatística é adequada?** Usamos mediana e IQR em vez de média e desvio padrão,
porque todas as distribuições são assimétricas com cauda longa; a média seria dominada pelos
extremos. Nas correlações usamos Spearman, que trabalha com postos e não pressupõe
normalidade nem linearidade, o que é adequado para distribuições como as observadas. O grande
número de empates em zero no CFR (a) é tratado pela média dos postos.

Nos testes por subgrupo da RQ 06 são feitas 30 comparações simultâneas, o que inflaria o erro
tipo I; aplicamos a correção de **Holm**, mais conservadora que o nível nominal de 5%. Os
tamanhos de efeito são reportados junto dos p-valores (ε² e Cliff's delta), porque
significância estatística com n = 350 não implica relevância prática.

Alguns subgrupos são pequenos. O tipo do projeto, usado como fator na RQ 06, só existe para
os 60 repositórios da amostra-ouro, e os testes sobre ele têm poder reduzido: um resultado não
significativo ali não deve ser lido como ausência de efeito.

O tempo de recuperação é calculado sobre 330 repositórios; os 20 sem episódio na janela são
reportados à parte, e não imputados. A censura dentro da janela mostrou-se desprezível — 70,9%
dos repositórios não têm nenhum episódio censurado —, o que reduz o risco de subestimação da
mediana.

Por fim, uma ressalva sobre o próprio kappa. O coeficiente da dimensão "releases são entregas
reais" (0,745) é o menor dos três, mas isso não indica ambiguidade: o consenso classificou 59
dos 60 repositórios na mesma categoria, e sob distribuições tão concentradas o kappa penaliza
fortemente uma única divergência, embora a concordância bruta seja de 98,3%. Reportamos a
distribuição dos rótulos ao lado do coeficiente para evitar essa leitura equivocada.
