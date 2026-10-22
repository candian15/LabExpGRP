# Histórico da heurística de release corretiva (CFR b)

Cada versão testada contra o consenso da amostra-ouro e o F1 obtido. Se o F1 ficar
abaixo de 0,70, a heurística é refinada e reavaliada (seção 6 do enunciado).
O conteúdo vai para a Metodologia do artigo.

## Versões

| Versão | Regra |
|---|---|
| v1 | só mudança de *patch* no SemVer **ou** algum commit com `fix`/`revert`/`hotfix` no assunto |
| v2 | só *patch* **ou** pelo menos metade dos commits são correções |
| v3 | (só *patch* **e** algum commit de correção) **ou** pelo menos metade dos commits são correções |
| v4 | as *release notes* têm seção de correção e nenhuma de novidade, **ou** é *patch* com pelo menos 30% de correções entre os commits substantivos (fora manutenção, dependências e infraestrutura) |

Para testar uma nova regra, acrescente uma função em `metricas/cfr_entrega.py`, registre-a em
`HEURISTICAS` e descreva-a na tabela acima.

## Resultados

Gerados por `python -m validacao.avaliar_heuristica --registrar --nota "..."`
(depois que o `validacao/consenso.csv` estiver commitado). As rodadas aparecem abaixo.

### Rodada de 2026-10-21

rodada contra o consenso revisado

| Versão | n | VP | FP | FN | VN | Precisão | Recall | F1 | F1 ≥ 0,70 |
|---|---|---|---|---|---|---|---|---|---|
| v1 | 299 | 110 | 170 | 1 | 18 | 0.39 | 0.99 | 0.56 | não |
| v2 | 299 | 84 | 74 | 27 | 114 | 0.53 | 0.76 | 0.62 | não |
| v3 | 299 | 71 | 67 | 40 | 121 | 0.51 | 0.64 | 0.57 | não |

### Rodada de 2026-10-21

v4: release notes só de correção, ou patch com pelo menos 30% de correções entre os commits substantivos

| Versão | n | VP | FP | FN | VN | Precisão | Recall | F1 | F1 ≥ 0,70 |
|---|---|---|---|---|---|---|---|---|---|
| v1 | 299 | 110 | 170 | 1 | 18 | 0.39 | 0.99 | 0.56 | não |
| v2 | 299 | 84 | 74 | 27 | 114 | 0.53 | 0.76 | 0.62 | não |
| v3 | 299 | 71 | 67 | 40 | 121 | 0.51 | 0.64 | 0.57 | não |
| v4 | 299 | 72 | 33 | 39 | 155 | 0.69 | 0.65 | 0.67 | não |
