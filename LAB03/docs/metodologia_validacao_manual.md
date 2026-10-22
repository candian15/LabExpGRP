# Metodologia: protocolo de validação manual

> Parte do Pedro na seção de Metodologia. Os números saem de `validacao/kappa.csv` e
> `validacao/consenso*.csv`, gerados por `kappa_fleiss.py` e `consenso.py`. A versão condensada,
> usada no artigo, está em `metodologia_validacao_manual.tex`.

## Validação manual

Como as métricas dependem de *proxies* e de uma heurística automática para identificar
releases corretivas, comparamos parte dos dados com o julgamento humano. Sorteamos uma
amostra-ouro de 60 repositórios da amostra final (`df.sample(n=60, random_state=42)`,
após ordenar os repositórios pelo nome) e, para cada um, 5 releases da janela (mesma
semente). Só entraram no sorteio as releases com release anterior e comparação de commits
disponível, porque sem a lista de commits não é possível julgar se uma release é corretiva.
Um repositório tinha menos de 5 releases nessa condição, e a amostra ficou com 299
releases.

Os três autores rotularam a amostra de forma independente, sem consultar uns aos
outros e sem acesso à saída da heurística. Cada um classificou: (i) o tipo do projeto
(biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro); (ii) se as releases do
repositório representam entregas reais ao usuário (sim, não ou incerto); e (iii) para
cada release sorteada, se ela é corretiva (sim ou não), a partir das *release notes* e
da lista de commits. As planilhas foram geradas automaticamente, com links diretos para
cada release e para a comparação de commits, e o critério de cada rótulo foi definido por
escrito antes da rotulagem (`validacao/PROTOCOLO.md`).

A concordância entre os avaliadores foi medida pelo kappa de Fleiss em cada dimensão,
que desconta a concordância esperada por acaso, e interpretada pela escala de Landis e
Koch (1977). A tabela abaixo resume os resultados.

| Dimensão | Itens | κ de Fleiss | Concordância |
|---|---|---|---|
| Tipo do projeto | 60 | 0,835 | Quase perfeita |
| Releases são entregas reais | 60 | 0,745 | Substancial |
| Release corretiva | 299 | 0,876 | Quase perfeita |

O menor kappa é o de "releases são entregas reais" (0,745), e o motivo é o desbalanceamento
dos rótulos, não a ambiguidade do critério. O consenso classificou 59 dos 60
repositórios como `sim` e apenas um como `incerto`, de modo que a concordância esperada
por acaso é muito alta e uma única divergência (o `BtbN/FFmpeg-Builds`, que publica
binários por automação mensal) já derruba o coeficiente. A concordância bruta nessa
dimensão é de 98,3% (59 de 60). O kappa se comporta assim sempre que os rótulos se
concentram numa categoria, e por isso reportamos também a distribuição dos rótulos.

A dimensão mais ambígua é o tipo do projeto (0,835), com 9 divergências em
60. Elas se concentram em dois limites: o que separa biblioteca de aplicação em projetos
que entregam ao mesmo tempo um servidor e um SDK (`vllm-project/vllm`,
`sgl-project/sglang-omni`, `rerun-io/rerun` e `Skyvern-AI/skyvern`) e o alcance da
categoria `outro`, usada por parte dos avaliadores para extensões de banco de dados e
repositórios de automação de *builds* (`timescale/timescaledb`, `BtbN/FFmpeg-Builds`).

Na dimensão que interessa à heurística, release corretiva, o kappa é de 0,876, com 26
divergências em 299. O critério não é inteiramente objetivo nem para humanos, porque
releases que misturam correções e novidades admitem leitura dupla. Como a heurística
automática da seção anterior é avaliada contra o consenso desses mesmos avaliadores, esse
valor serve de teto prático para ela.

O *rótulo de consenso* foi definido por maioria simples (pelo menos 2 dos 3 avaliadores).
Os casos sem maioria (empates 1-1-1, possíveis nas dimensões com mais de duas categorias)
seriam decididos em reunião dos três autores, mas não houve nenhum. O consenso sobre o tipo do
projeto é usado como fator na RQ 06, e o consenso sobre releases corretivas é a referência
para avaliar a heurística do CFR (b), descrita na seção anterior.
