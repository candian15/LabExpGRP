# RQ03 + RQ04 — Extração via GitHub GraphQL API

Parte individual referente ao **Lab01S01**, cobrindo:

- **RQ03.** Sistemas populares lançam releases com frequência?
  Métrica: total de releases (`releases.totalCount`).
- **RQ04.** Sistemas populares são atualizados com frequência?
  Métrica: tempo até a última atualização (`pushedAt` até a data atual).

## Estrutura

```
.
└── rq03_rq04_extract.py   # script principal
```

## Setup

```bash
pip install requests
export GITHUB_TOKEN="seu_token_aqui"
```

Token: gere em https://github.com/settings/tokens (classic), escopo `public_repo` já basta (somente leitura).

## Execução

```bash
# 1. Validação rápida (8 repositórios de amostra)
python rq03_rq04_extract.py --sample

# 2. Execução completa (100 repositórios)
python rq03_rq04_extract.py
```

Saída: `sample_rq03_rq04.csv` (amostra) ou `rq03_rq04.csv` (completo), com colunas:

| coluna | descrição |
|---|---|
| repo | nome do repositório (`owner/name`) |
| stars | número de estrelas |
| total_releases | total de releases publicadas (`releases.totalCount`) |
| pushed_at | data do último push no repositório (ISO 8601) |
| days_since_update | dias desde o último push, calculado a partir de pushed_at |

## Critério de seleção dos repositórios

Query de busca: `stars:>1000 sort:stars-desc`, via `search(type: REPOSITORY)`.
Mesmo critério usado pelos demais integrantes (RQ01–06 + bônus), garantindo que os 100 repositórios extraídos sejam idênticos entre as partes, permitindo o merge dos datasets por `repo`.

## Validação

Antes de rodar os 100 completos, os valores da amostra (`--sample`) foram conferidos manualmente comparando:
- `total_releases` com a contagem exibida na aba *Releases* do repositório;
- `pushed_at` com a data do commit mais recente na branch padrão.

## Observações

- Foi usado `pushedAt` (data do último push de código) em vez de `updatedAt` (que também muda por eventos de metadados, como estrelas e configurações), por ser um proxy mais fiel de "atualização" do sistema para a RQ04.
- Recomenda-se reportar a **mediana** de `days_since_update` além da média, para reduzir efeito de outliers (repositórios recém-atualizados vs. abandonados).
