# RQ05 + RQ06 — Linguagem primária e issues fechadas

- **RQ05.** Sistemas populares são escritos nas linguagens mais populares?
  Métrica: linguagem primária de cada repositório (`primaryLanguage`).
- **RQ06.** Sistemas populares possuem um alto percentual de issues fechadas?
  Métrica: razão entre issues fechadas e total de issues (`issues(states: CLOSED)` / `issues`).

## Estrutura

```
.
├── rq05_rq06_extract.py         # extração via GraphQL (GitHub API)
├── analyze_rq05_rq06.py         # checagem de consistência (contagem por linguagem, outliers via IQR)
└── visualize_rq05_rq06.py       # gera o gráfico de barras (RQ05) e o histograma (RQ06)
```

## Setup

```bash
export GITHUB_TOKEN="seu_token_aqui"
```

Token: gere em https://github.com/settings/tokens (classic), escopo `public_repo` já basta (somente leitura). Extração feita só com a stdlib (`urllib`), sem bibliotecas de terceiros para consultar a API do GitHub.

## Execução

```bash
# 1. Validação rápida (8 repositórios de amostra)
python rq05_rq06_extract.py --sample

# 2. Coleta de 100 repositórios (Lab01S01)
python rq05_rq06_extract.py

# 3. Coleta completa de 1000 repositórios, com paginação (Lab01S02)
python rq05_rq06_extract.py --full

# 4. Checagem de consistência (contagem por linguagem, distribuição, outliers)
python analyze_rq05_rq06.py rq05_rq06_1000.csv

# 5. Visualização (barras por linguagem + histograma da razão de issues fechadas)
python visualize_rq05_rq06.py rq05_rq06_1000.csv
```

Saída da extração: `sample_rq05_rq06.csv` (`--sample`), `rq05_rq06.csv` (100) ou `rq05_rq06_1000.csv` (`--full`), com colunas:

| coluna | descrição |
|---|---|
| repo | nome do repositório (`owner/name`) |
| stars | número de estrelas |
| primary_language | linguagem primária (`primaryLanguage.name`), `"N/A"` se não detectada |
| closed_issues | total de issues fechadas |
| total_issues | total de issues (abertas + fechadas) |
| closed_issue_ratio | `closed_issues / total_issues`, `"N/A"` quando `total_issues == 0` |

> **Nota:** o CSV de 1000 repositórios (`rq05_rq06_1000.csv`) não está commitado neste repositório — precisa ser gerado localmente com `--full` antes de rodar `analyze_rq05_rq06.py`/`visualize_rq05_rq06.py`, e também é uma das entradas do [RQ07](../RQ07/README.md). Veja a pendência equivalente no [README do LAB01](../README.md#pendências-conhecidas).

## Critério de seleção dos repositórios

Query de busca: `stars:>1000 sort:stars-desc`, via `search(type: REPOSITORY)`.
Mesmo critério usado pelos demais integrantes (RQ01–07), garantindo que os repositórios extraídos sejam idênticos entre as partes, permitindo o merge dos datasets por `repo`.

## Observações

- Para RQ05 (categórica), a métrica reportada é contagem/percentual por linguagem, não média/mediana — por isso `visualize_rq05_rq06.py` usa um gráfico de barras em vez de histograma.
- Para "linguagens mais populares" como referência externa (comparação com a RQ05), definir e citar explicitamente a fonte usada (ex.: TIOBE Index, GitHut ou GitHub Octoverse) no relatório final, mantendo a mesma referência em todo o laboratório — isso ainda precisa ser feito na análise/relatório, não faz parte da extração.
