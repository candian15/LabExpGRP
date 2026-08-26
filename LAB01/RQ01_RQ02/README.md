# RQ01 + RQ02 — Idade dos repositórios e contribuição externa

- **RQ01.** Sistemas populares são maduros/antigos?
  Métrica: idade do repositório (`createdAt` até a data atual).
- **RQ02.** Sistemas populares recebem muita contribuição externa?
  Métrica: total de pull requests aceitas (`pullRequests(states: MERGED)`).

## Estrutura

```
.
├── rq01_rq02_extract.py         # extração via GraphQL (GitHub API)
├── analyze_rq01_rq02.py         # checagem de consistência (ausentes, outliers via IQR)
├── visualize_rq01_rq02.py       # gera os histogramas de RQ01 e RQ02
├── rq01_rq02_real_sample.csv    # amostra usada para validação manual
├── rq01_idade_histograma.png
└── rq02_prs_histograma.png
```

## Setup

```bash
export GITHUB_TOKEN="seu_token_aqui"
```

Token: gere em https://github.com/settings/tokens (classic), escopo `public_repo` já basta (somente leitura). Não é necessário instalar nada além da stdlib — a extração usa `urllib`, sem bibliotecas de terceiros para consultar a API do GitHub (exigência do enunciado).

## Execução

```bash
# 1. Validação rápida (8 repositórios de amostra)
python rq01_rq02_extract.py --sample

# 2. Coleta de 100 repositórios (Lab01S01)
python rq01_rq02_extract.py

# 3. Coleta completa de 1000 repositórios, com paginação (Lab01S02)
python rq01_rq02_extract.py --full

# 4. Checagem de consistência (ausentes, distribuição, outliers)
python analyze_rq01_rq02.py rq01_rq02_1000.csv

# 5. Visualização (histogramas)
python visualize_rq01_rq02.py rq01_rq02_1000.csv
```

Saída da extração: `sample_rq01_rq02.csv` (`--sample`), `rq01_rq02.csv` (100) ou `rq01_rq02_1000.csv` (`--full`), com colunas:

| coluna | descrição |
|---|---|
| repo | nome do repositório (`owner/name`) |
| stars | número de estrelas |
| created_at | data de criação (ISO 8601) |
| age_years | idade em anos, calculada a partir de created_at |
| merged_prs | total de pull requests aceitas (mergeadas) |

O CSV de 1000 repositórios (`rq01_rq02_1000.csv`) já está commitado neste diretório.

## Critério de seleção dos repositórios

Query de busca: `stars:>1000 sort:stars-desc`, via `search(type: REPOSITORY)`.
Mesmo critério usado pelos demais integrantes (RQ01–07), garantindo que os repositórios extraídos sejam idênticos entre as partes, permitindo o merge dos datasets por `repo`.

## Validação

Antes de rodar os 100/1000 completos, os valores da amostra (`--sample`) foram conferidos manualmente comparando:
- `created_at` com a data mostrada na página inicial do repositório no GitHub;
- `merged_prs` com a contagem da aba *Pull Requests* filtrando por `is:merged`.

## Observações

- `pullRequests(states: MERGED)` conta todas as PRs mergeadas (mantenedores inclusos), usada como proxy de contribuição externa.
- É reportada a **mediana** da idade e de PRs além da média, para reduzir o efeito de outliers — confirmado necessário pela checagem de consistência (`analyze_rq01_rq02.py`), que usa o método IQR para detectar outliers.
