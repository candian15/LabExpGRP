# RQ03 + RQ04 — Releases e frequência de atualização

- **RQ03.** Sistemas populares lançam releases com frequência?
  Métrica: total de releases (`releases.totalCount`).
- **RQ04.** Sistemas populares são atualizados com frequência?
  Métrica: tempo até a última atualização (`pushedAt` até a data atual).

## Estrutura

```
.
├── rq03_rq04_extract.py           # extração via GraphQL (GitHub API)
├── visualize_rq03_rq04.py         # gera os histogramas de RQ03 e RQ04
├── sample_rq03_rq04.csv           # amostra usada para validação manual
├── rq03_rq04_1000.csv             # dataset completo (1000 repositórios)
├── rq03_releases_histograma.png
└── rq04_dias_histograma.png
```

## Setup

```bash
export GITHUB_TOKEN="seu_token_aqui"
```

Token: gere em https://github.com/settings/tokens (classic), escopo `public_repo` já basta (somente leitura). Extração feita só com a stdlib (`urllib`), sem bibliotecas de terceiros para consultar a API do GitHub.

## Execução

```bash
# 1. Validação rápida (8 repositórios de amostra)
python rq03_rq04_extract.py --sample

# 2. Coleta de 100 repositórios (Lab01S01)
python rq03_rq04_extract.py

# 3. Coleta completa de 1000 repositórios, com paginação (Lab01S02)
python rq03_rq04_extract.py --full

# 4. Visualização (histogramas em escala log)
python visualize_rq03_rq04.py rq03_rq04_1000.csv
```

Saída da extração: `sample_rq03_rq04.csv` (`--sample`), `rq03_rq04.csv` (100) ou `rq03_rq04_1000.csv` (`--full`), com colunas:

| coluna | descrição |
|---|---|
| repo | nome do repositório (`owner/name`) |
| stars | número de estrelas |
| total_releases | total de releases publicadas (`releases.totalCount`) |
| pushed_at | data do último push no repositório (ISO 8601) |
| days_since_update | dias desde o último push, calculado a partir de pushed_at |

## Critério de seleção dos repositórios

Query de busca: `stars:>1000 sort:stars-desc`, via `search(type: REPOSITORY)`.
Mesmo critério usado pelos demais integrantes (RQ01–07), garantindo que os repositórios extraídos sejam idênticos entre as partes, permitindo o merge dos datasets por `repo`.

## Validação

Antes de rodar os 100/1000 completos, os valores da amostra (`--sample`) foram conferidos manualmente comparando:
- `total_releases` com a contagem exibida na aba *Releases* do repositório;
- `pushed_at` com a data do commit mais recente na branch padrão.

## Observações

- Foi usado `pushedAt` (data do último push de código) em vez de `updatedAt` (que também muda por eventos de metadados, como estrelas e configurações), por ser um proxy mais fiel de "atualização" do sistema para a RQ04.
- Tanto `total_releases` quanto `days_since_update` são bem assimétricos (muitos repositórios com 0 releases ou atualizados há poucos dias, e uma cauda longa de outliers) — por isso os histogramas em `visualize_rq03_rq04.py` usam escala log, mesmo tratamento aplicado à RQ02.
- Recomenda-se reportar a **mediana** além da média para as duas métricas, para reduzir efeito de outliers.
