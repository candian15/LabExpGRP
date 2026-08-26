# RQ07 — Análise cruzada por linguagem

**RQ07.** Sistemas escritos em linguagens mais populares recebem mais contribuição externa, lançam mais releases e são atualizados com mais frequência?
Métrica: resultados de RQ02, RQ03 e RQ04, divididos por linguagem primária (RQ05).

Diferente das demais, esta parte **não consulta a API do GitHub** — ela só junta (merge) os CSVs já gerados por [RQ01_RQ02](../RQ01_RQ02/), [RQ03_RQ04](../RQ03_RQ04/) e [RQ05_RQ06](../RQ05_RQ06/), usando a coluna `repo` como chave, e agrega as métricas por linguagem.

## Estrutura

```
.
├── rq07_analysis.py       # junta os 3 datasets e agrega por linguagem (gera rq07_por_linguagem.csv)
└── visualize_rq07.py      # gera os gráficos de barras (mediana por linguagem)
```

## Execução

Precisa dos três CSVs de 1000 repositórios já gerados (veja os READMEs de cada RQ para como gerá-los):

```bash
python rq07_analysis.py \
    --rq02 ../RQ01_RQ02/rq01_rq02_1000.csv \
    --rq0304 ../RQ03_RQ04/rq03_rq04_1000.csv \
    --rq05 ../RQ05_RQ06/rq05_rq06_1000.csv

python visualize_rq07.py rq07_por_linguagem.csv
```

Um repositório só entra na análise se estiver presente nos três arquivos (inner join). A saída `rq07_por_linguagem.csv` tem uma linha por linguagem, com a contagem de repositórios e a mediana de cada métrica.

## Observações

- `visualize_rq07.py` só considera linguagens com pelo menos `MIN_REPOS = 10` repositórios (evita medianas pouco confiáveis) e mostra as `TOP = 10` linguagens mais frequentes.
- Leitura das métricas: PRs e releases **maiores** = mais contribuição/atividade; dias sem update **menores** = atualização mais frequente.
- [RQ01_RQ02](../RQ01_RQ02/rq01_rq02_1000.csv) e [RQ03_RQ04](../RQ03_RQ04/rq03_rq04_1000.csv) já têm o CSV de 1000 repositórios commitado; falta o de RQ05_RQ06 para rodar `rq07_analysis.py` — veja a pendência no [README do LAB01](../README.md#pendências-conhecidas).
