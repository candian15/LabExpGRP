# Metodologia: definições operacionais e heurística de release corretiva

> Parte do Arthur na seção de Metodologia. Os números da heurística saem de
> `validacao/historico_heuristica.md`, gerado por `avaliar_heuristica.py`. A versão condensada,
> usada no artigo, está em `metodologia_definicoes_heuristica.tex`.

## Definições operacionais

Seguimos as definições comuns da disciplina. Como o GitHub não registra *deploys* nem
falhas em produção, todas as métricas são medidas por *proxies*:

- **Deploy:** release publicada (`draft = false`), no *default branch*. Pré-releases e
  tags sem release ficam fora da definição principal e entram só como variantes na análise
  de sensibilidade.
- **Deployment frequency:** releases publicadas na janela dividido pelo número de semanas
  da janela (12 meses).
- **Lead time for changes**, em duas variantes. Para cada release R, os commits incluídos
  são obtidos comparando R com a release anterior (`compare/{anterior}...{R}`), usando
  `commit.author.date`. Em (a), o lead time de R é a diferença entre a data de R e a do
  commit mais antigo incluído, e o valor do repositório é a mediana entre as releases. Em
  (b), cada commit tem seu lead time e o valor do repositório é a mediana de todos os
  commits de todas as releases. A primeira release da história do repositório e as
  releases cujo `compare` retorna 404 são ignoradas, e a quantidade é registrada.
- **Change failure rate**, em duas variantes. Em (a), a proporção de *workflow runs* de
  `push` com falha (`failure`, `timed_out`, `startup_failure`) entre falhas e sucessos;
  ela mede falha de *pipeline*, não de produção. Em (b), descrita abaixo, a proporção de
  releases seguidas de uma release corretiva em até 7 dias.
- **Tempo de recuperação:** dentro de cada workflow, do início da primeira falha após um
  sucesso até o fim do próximo sucesso, com mediana por repositório. Episódios que não
  terminam na janela são censurados e reportados, não descartados.

## CFR (b): proxy de entrega

Uma release R é considerada falha se for seguida, em até 7 dias, por uma release
corretiva, isto é, uma release cujo objetivo principal é corrigir um defeito recente. O
CFR (b) do repositório é `releases que falharam ÷ releases avaliadas`. Releases publicadas
nos últimos 7 dias da janela não podem ser avaliadas e ficam fora do denominador
(censura); o número de releases censuradas é reportado.

Como o GitHub não indica se uma release é corretiva, usamos uma heurística automática
sobre a versão (SemVer) e o assunto dos commits entre a release e a anterior. Decisões
de projeto: (i) R é comparada apenas com a release seguinte; (ii) lemos só o assunto do
commit, porque o corpo costuma citar "fixes #123" também em funcionalidades novas; (iii) se
o `compare` falha, vale apenas o critério de versão; (iv) a primeira release da história
nunca é corretiva.

Testamos quatro versões:

| Versão | Regra |
|---|---|
| v1 | só mudança de *patch* (`2.3.0 → 2.3.1`) **ou** algum commit com `fix`, `revert` ou `hotfix` no assunto |
| v2 | só *patch* **ou** pelo menos metade dos commits são correções |
| v3 | (só *patch* **e** algum commit de correção) **ou** pelo menos metade dos commits são correções |
| v4 | as *release notes* têm seção de correção e nenhuma de novidade **ou** (só *patch* **e** algum commit de correção entre os substantivos), descrita adiante |

### Validação da heurística

Sorteamos 60 repositórios da amostra final (`random_state = 42`) e 5 releases de cada um.
Os três integrantes rotularam, de forma independente e sem ver a saída da heurística, se
cada release é corretiva; o consenso foi definido conforme o protocolo descrito na seção
de validação manual. Comparamos a heurística com o consenso por precisão, recall e F1 da
classe "corretiva" (`precision_recall_fscore_support`, scikit-learn), com limiar de
F1 ≥ 0,70 para aceitar a heurística.

| Versão | VP | FP | FN | VN | Precisão | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | 110 | 170 | 1 | 18 | 0,39 | 0,99 | 0,56 |
| v2 | 84 | 74 | 27 | 114 | 0,53 | 0,76 | 0,62 |
| v3 | 71 | 67 | 40 | 121 | 0,51 | 0,64 | 0,57 |
| v4 | 81 | 57 | 30 | 131 | 0,59 | 0,73 | **0,65** |

A v4 foi a escolhida, com F1 de 0,65. Nenhuma versão atingiu o limiar de 0,70, e isso
é reportado como limitação nas ameaças à validade.

As três primeiras versões partem da mesma suposição: toda mudança de *patch* no SemVer seria
correção de defeito. Publicar *patch* é a prática recomendada pelo próprio SemVer
e não implica corrigir nada, de modo que a v1 marcou 170 releases que o consenso considerou
não corretivas. Ela acerta quase todas as corretivas (recall 0,99) ao custo de dizer "sim"
para quase tudo (precisão 0,39). A v3 tentou apertar o critério exigindo também um commit de
correção, mas perdeu corretivas verdadeiras sem ganhar precisão.

A v4 troca o critério isolado de *patch* por dois sinais. O primeiro são as *release notes*:
quando elas trazem uma seção de correção e nenhuma de novidade, 88% das releases da
amostra-ouro são corretivas pelo consenso, contra 56% quando o único sinal é a mudança de
*patch*. O segundo é a exigência de pelo menos um commit de correção entre os
*substantivos*, isto é, descontando manutenção, dependências e infraestrutura (`chore`,
`ci`, `docs`, `test`, `bump`). Sem esse desconto, uma release de *patch* composta apenas de
atualizações automáticas de dependência seria classificada como corretiva, que é o caso mais
frequente entre os falsos positivos da v1.

Quase todo o ganho vem da precisão, que sobe de 0,39 na v1 para 0,59: os falsos positivos caem
de 170 para 57, com recall de 0,73. Permanecem 30 falsos negativos, em sua maioria
releases grandes de projetos que não seguem SemVer e cujas notas misturam correções e
novidades, os mesmos casos em que os avaliadores também divergiram.

Nenhum dos critérios usa limiar numérico ajustado. A regra é composta de condições binárias
e pode ser aplicada a outra amostra sem calibração.
