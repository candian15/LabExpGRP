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

Para testar uma nova regra, acrescente uma função em `metricas/cfr_entrega.py`, registre-a em
`HEURISTICAS` e descreva-a na tabela acima.

## Resultados

Gerados por `python -m validacao.avaliar_heuristica --registrar --nota "..."`
(depois que o `validacao/consenso.csv` estiver commitado). As rodadas aparecem abaixo.
