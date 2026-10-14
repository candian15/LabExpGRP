# Metodologia — definições operacionais e heurística de release corretiva

> Rascunho da parte do Artur na seção de Metodologia. Os trechos entre `[[ ]]` só podem
> ser preenchidos depois da validação manual (consenso do grupo + `avaliar_heuristica.py`).

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

Uma release R é considerada **falha** se for seguida, em até **7 dias**, por uma **release
corretiva**, isto é, uma release cujo objetivo principal é corrigir um defeito recente. O
CFR (b) do repositório é `releases que falharam ÷ releases avaliadas`. Releases publicadas
nos últimos 7 dias da janela não podem ser avaliadas e ficam fora do denominador
(censura); o número de releases censuradas é reportado.

Como o GitHub não indica se uma release é corretiva, usamos uma heurística automática
sobre a versão (SemVer) e o **assunto** dos commits entre a release e a anterior. Decisões
de projeto: (i) R é comparada apenas com a **release seguinte**; (ii) lemos só o assunto do
commit, porque o corpo costuma citar "fixes #123" também em funcionalidades novas; (iii) se
o `compare` falha, vale apenas o critério de versão; (iv) a primeira release da história
nunca é corretiva.

Testamos as seguintes versões:

| Versão | Regra |
|---|---|
| v1 | só mudança de *patch* (`2.3.0 → 2.3.1`) **ou** algum commit com `fix`, `revert` ou `hotfix` no assunto |
| v2 | só *patch* **ou** pelo menos metade dos commits são correções |
| v3 | (só *patch* **e** algum commit de correção) **ou** pelo menos metade dos commits são correções |

### Validação da heurística

Sorteamos 60 repositórios da amostra final (`random_state = 42`) e 5 releases de cada um.
Os três integrantes rotularam, de forma independente e sem ver a saída da heurística, se
cada release é corretiva; o consenso foi definido conforme o protocolo descrito na seção
de validação manual. Comparamos a heurística com o consenso por precisão, recall e F1 da
classe "corretiva" (`precision_recall_fscore_support`, scikit-learn), com limiar de
F1 ≥ 0,70 para aceitar a heurística.

[[ Tabela com v1, v2, v3: precisão, recall e F1 (copiar de validacao/historico_heuristica.md) ]]

[[ Versão escolhida, F1 obtido e o que as versões anteriores erravam (falsos positivos e falsos negativos mais comuns) ]]
