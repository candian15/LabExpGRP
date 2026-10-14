# Metodologia — protocolo de validação manual

> Rascunho da parte do Pedro na seção de Metodologia. Os trechos entre `[[ ]]` só podem ser
> preenchidos depois da rotulagem (`kappa_fleiss.py` e `consenso.py`). A versão LaTeX está
> em `metodologia_validacao_manual.tex`.

## Validação manual

Como as métricas dependem de *proxies* e de uma heurística automática para identificar
releases corretivas, comparamos parte dos dados com o julgamento humano. Sorteamos uma
**amostra-ouro** de 60 repositórios da amostra final (`df.sample(n=60, random_state=42)`,
após ordenar os repositórios pelo nome) e, para cada um, 5 releases da janela (mesma
semente). Só entraram no sorteio as releases com release anterior e comparação de commits
disponível, porque sem a lista de commits não é possível julgar se uma release é corretiva.
[[N]] repositórios tinham menos de 5 releases nessa condição, e a amostra ficou com [[N]]
releases.

Os três autores rotularam a amostra **de forma independente**, sem consultar uns aos
outros e sem acesso à saída da heurística. Cada um classificou: (i) o **tipo do projeto**
(biblioteca/framework, aplicação/serviço, ferramenta CLI ou outro); (ii) se as releases do
repositório **representam entregas reais ao usuário** (sim, não ou incerto); e (iii) para
cada release sorteada, se ela é **corretiva** (sim ou não), a partir das *release notes* e
da lista de commits. As planilhas foram geradas automaticamente, com links diretos para
cada release e para a comparação de commits, e o critério de cada rótulo foi definido por
escrito antes da rotulagem (`validacao/PROTOCOLO.md`).

A concordância entre os avaliadores foi medida pelo **kappa de Fleiss** em cada dimensão,
que desconta a concordância esperada por acaso, e interpretada pela escala de Landis e
Koch (1977). A Tabela [[X]] resume os resultados.

| Dimensão | Itens | κ de Fleiss | Concordância |
|---|---|---|---|
| Tipo do projeto | 60 | [[κ]] | [[ ]] |
| Releases são entregas reais | 60 | [[κ]] | [[ ]] |
| Release corretiva | [[N]] | [[κ]] | [[ ]] |

[[Comentar a dimensão com menor kappa: um valor baixo indica que o critério é ambíguo
mesmo para humanos, o que limita o quanto se pode esperar da heurística automática.]]

O **rótulo de consenso** foi definido por maioria simples (pelo menos 2 dos 3 avaliadores).
Os casos sem maioria (empates 1-1-1, possíveis nas dimensões com mais de duas categorias)
foram decididos em reunião dos três autores ([[n]] casos). O consenso sobre o tipo do
projeto é usado como fator na RQ 06, e o consenso sobre releases corretivas é a referência
para avaliar a heurística do CFR (b), descrita na seção anterior.
