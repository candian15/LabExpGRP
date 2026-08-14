# RQ01 + RQ02 — Extração via GitHub GraphQL API

Parte individual referente ao **Lab01S01**, cobrindo:

- **RQ01.** Sistemas populares são maduros/antigos?
  Métrica: idade do repositório (`createdAt` até a data atual).
- **RQ02.** Sistemas populares recebem muita contribuição externa?
  Métrica: total de pull requests aceitas (`pullRequests(states: MERGED)`).

## Estrutura

```
.
├── rq01_rq02_extract.py   # script principal
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # depois edite o .env com seu token
export $(cat .env | xargs)  # ou exporte manualmente: export GITHUB_TOKEN=...
```

Token: gere em https://github.com/settings/tokens (classic), escopo `public_repo` já basta (somente leitura).

## Execução

```bash
# 1. Validação rápida (8 repositórios de amostra)
python rq01_rq02_extract.py --sample

# 2. Execução completa (100 repositórios)
python rq01_rq02_extract.py
```

Saída: `sample_rq01_rq02.csv` (amostra) ou `rq01_rq02.csv` (completo), com colunas:

| coluna | descrição |
|---|---|
| repo | nome do repositório (`owner/name`) |
| stars | número de estrelas |
| created_at | data de criação (ISO 8601) |
| age_years | idade em anos, calculada a partir de created_at |
| merged_prs | total de pull requests aceitas (mergeadas) |

## Critério de seleção dos repositórios

Query de busca: `stars:>1000 sort:stars-desc`, via `search(type: REPOSITORY)`.
Este critério deve ser o mesmo usado pelos demais integrantes para garantir que os 100 repositórios extraídos sejam idênticos entre as partes (RQ01–06 + bônus), permitindo o merge dos datasets por `repo`.

## Validação

Antes de rodar os 100 completos, os valores da amostra (`--sample`) foram conferidos manualmente comparando:
- `created_at` com a data mostrada na página inicial do repositório no GitHub;
- `merged_prs` com a contagem da aba *Pull Requests* filtrando por `is:merged`.

## Observações

- `pullRequests(states: MERGED)` conta todas as PRs mergeadas (mantenedores inclusos), usada como proxy de contribuição externa para este sprint.
- Recomenda-se reportar a **mediana** da idade além da média, para reduzir efeito de outliers.
