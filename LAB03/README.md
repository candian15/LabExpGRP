# LAB03: mineração de métricas DORA

Pipeline que calcula as quatro métricas DORA a partir dos dados públicos de repositórios
open-source que usam GitHub Actions, e classifica cada repositório em Elite / High / Medium / Low.

A coleta é feita por script próprio, direto nas APIs REST do GitHub (nenhuma biblioteca de
acesso ao GitHub, como PyGithub).

## Setup

```bash
cd LAB03
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_...                       # Windows: $env:GITHUB_TOKEN="ghp_..."
```

O token é lido **só** da variável de ambiente `GITHUB_TOKEN` e nunca é commitado. Um token
clássico sem escopos (apenas leitura de dados públicos) é suficiente.

## Rodar

```bash
python -m pipeline --config config.yaml
```

Esse é o único comando necessário. Ele busca os candidatos, aplica os filtros de inclusão,
coleta releases/commits/workflow runs dos selecionados, calcula as métricas e escreve os CSVs
em `dados/`.

Cada resposta da API é gravada em `cache/`, então **rodar o comando de novo continua de onde
parou**: se a coleta cair por rate limit, queda de rede ou `Ctrl+C`, nenhuma chamada já feita é
repetida. Para recoletar do zero, apague `cache/`.

A coleta completa demora horas e bate no rate limit várias vezes (o script espera sozinho e
continua). Para testar, baixe `max_repositorios` para 2 ou 3 antes de rodar a amostra inteira.

### config.yaml

| Chave | O que faz |
|---|---|
| `janela.inicio` / `janela.fim` | Janela de observação (12 meses, datas fixadas pelo professor). Inclusiva nas duas pontas |
| `busca.faixas_estrelas` | Faixas de `stars:` consultadas. A busca devolve no máximo 1.000 resultados por consulta, então faixas largas precisam ser fatiadas |
| `busca.linguagens` | Vazio = todas. Preencher fatia a busca ainda mais (`language:`) |
| `selecao.min_releases` / `min_runs` | Critério mínimo de inclusão (5 releases e 50 runs válidos na janela) |
| `selecao.max_repositorios` | Para a coleta ao fechar essa quantidade de repositórios aprovados |
| `selecao.contribuidores` | Conta contribuidores dos aprovados (1 chamada extra cada), para os quartis da RQ 06 |
| `cache` / `saida` | Pastas do cache da API e dos CSVs |

## Saídas

`dados/funil.csv` — quantos repositórios sobraram em cada etapa da seleção e o motivo de cada
descarte (tabela da seção de Metodologia do artigo):

| Coluna | Tipo | Significado |
|---|---|---|
| `etapa` | texto | Critério aplicado, na ordem em que a seleção aplica os filtros |
| `restantes` | inteiro | Repositórios que ainda estavam na amostra depois da etapa |
| `descartados` | inteiro | Quantos a etapa descartou |
| `motivo_do_descarte` | texto | Por que os descartados saíram |

`dados/repositorios.csv` — uma linha por repositório **avaliado** (os descartados ficam na
tabela, com as métricas em branco e o motivo preenchido).

### Dicionário de dados de `repositorios.csv`

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `repo` | texto | — | `full_name` da API (`owner/nome`) |
| `estrelas` | inteiro | — | `stargazers_count` |
| `linguagem` | texto | — | `language` (vazio quando a API não define) |
| `default_branch` | texto | — | `default_branch`; é o único branch considerado |
| `criado_em` | data | ISO | `created_at` (UTC) |
| `idade_anos` | decimal | anos | `(fim da janela − created_at) / 365,25` |
| `contribuidores` | inteiro | — | última página de `/contributors?per_page=1&anon=true` |
| `n_releases` | inteiro | — | Releases publicadas na janela (`draft = false`, sem pré-releases) |
| `n_runs_validos` | inteiro | — | Workflow runs de `push` no default branch na janela com `conclusion` de sucesso ou falha |
| `deployment_frequency` | decimal | releases/semana | **RQ 01**: `n_releases / semanas da janela` |
| `lead_time_a_horas` | decimal | horas | **RQ 02a**: mediana, por release, de `published_at − data do commit mais antigo da release` |
| `lead_time_b_horas` | decimal | horas | **RQ 02b**: mediana de `published_at − data do commit`, sobre todos os commits de todas as releases |
| `cfr_ci` | decimal | fração 0–1 | **RQ 03a**: `falhas / (falhas + sucessos)` nos runs válidos |
| `recuperacao_horas` | decimal | horas | **RQ 04**: mediana dos episódios de falha (`updated_at` do sucesso − `run_started_at` da primeira falha), por workflow |
| `n_episodios` | inteiro | — | Episódios de falha encontrados (concluídos + censurados) |
| `prop_censurados` | decimal | fração 0–1 | Episódios que não terminaram dentro da janela |
| `releases_404` | inteiro | — | Releases ignoradas no lead time porque o `compare` deu 404 (tag apagada/reescrita) |
| `nota_frequencia`, `nota_lead_time`, `nota_cfr`, `nota_recuperacao` | inteiro | 1–4 | Nota de cada métrica: 4 Elite, 3 High, 2 Medium, 1 Low |
| `dora_nota` | inteiro | 1–4 | Mediana das quatro notas, arredondada para baixo |
| `dora` | texto | — | Nome da categoria de `dora_nota` |
| `motivo_descarte` | texto | — | Vazio = entrou na amostra; ver `funil.csv` |

A classificação é a combinação de referência **C1** da RQ 07: release como unidade de deploy,
lead time na variante (a) e CFR na variante (a).

## Módulos

| Arquivo | O que faz |
|---|---|
| [pipeline/\_\_main\_\_.py](pipeline/__main__.py) | Comando único: encadeia seleção, coleta, métricas e CSVs |
| [pipeline/github_client.py](pipeline/github_client.py) | Cliente HTTP: cache em disco, paginação, rate limit e backoff exponencial |
| [pipeline/selecao.py](pipeline/selecao.py) | Busca, metadados e filtros de inclusão |
| [pipeline/funil.py](pipeline/funil.py) | Tabela do funil de seleção |
| [pipeline/coleta_releases.py](pipeline/coleta_releases.py) | Releases e commits entre releases |
| [pipeline/coleta_runs.py](pipeline/coleta_runs.py) | Workflow runs, com a janela dividida por mês |
| [metricas/frequencia.py](metricas/frequencia.py) | Deployment frequency (RQ 01) |
| [metricas/lead_time.py](metricas/lead_time.py) | Lead time, variantes (a) e (b) (RQ 02) |
| [metricas/cfr.py](metricas/cfr.py) | Change failure rate, variante (a) (RQ 03) |
| [metricas/recuperacao.py](metricas/recuperacao.py) | Tempo de recuperação e censura (RQ 04) |
| [metricas/classificacao.py](metricas/classificacao.py) | Notas por métrica e categoria DORA (RQ 07) |

Os módulos de coleta também rodam sozinhos, para inspecionar um repositório:

```bash
python -m pipeline.coleta_releases psf/requests --inicio 2025-10-01 --fim 2026-09-30
python -m pipeline.coleta_runs     psf/requests --inicio 2025-10-01 --fim 2026-09-30
```

## Testes

```bash
pytest --cov=metricas --cov-report=term-missing
```

As funções de métrica são testadas com fixtures construídas à mão, incluindo os exemplos
numéricos do enunciado (lead time de 13 dias, recuperação de 1h20, notas 4-3-3-1 → High) e
casos de borda: release sem commits novos, falha nunca recuperada (censurada), runs
`cancelled` (ignorados) e métrica indisponível. Os mesmos testes rodam no GitHub Actions do
grupo a cada push ([.github/workflows/testes.yml](../.github/workflows/testes.yml)), com
`--cov-fail-under=80`.

## Definições operacionais e decisões do grupo

Seguimos as definições obrigatórias da seção 3 do enunciado. Onde o enunciado deixou a escolha
para o grupo, decidimos assim (tudo isso vai para a seção de Metodologia e para as ameaças à
validade):

- **Deploy** é release publicada (`draft = false`), sem pré-releases. Pré-releases e tags
  entram só como variantes na RQ 07.
- **Idade do repositório** é medida até o **fim da janela**, e não até "hoje", para que rodar o
  pipeline em outra data dê o mesmo número.
- **Ordem dos filtros**: Actions → releases → runs. Cada repositório recebe no máximo um motivo
  de descarte (o primeiro filtro que falhou), e o filtro mais caro é o último, para não gastar
  cota com quem já está fora.
- **Corte "1 por mês"** da classificação, que o enunciado dá em meses e a métrica mede em
  semanas: convertido por mês médio de 365,25/12 dias (≈ 0,23 release/semana), para que 12
  releases num ano caiam em Medium e não em Low.
- **Métrica indisponível** não recebe nota e fica fora da mediana da categoria geral (um
  repositório sem nenhuma release comparável, por exemplo, ainda é classificado pelas demais).
- **Falhas de CI antes do primeiro sucesso** do workflow na janela não abrem episódio de
  recuperação, porque o enunciado define o início do episódio como "primeira falha após um
  sucesso"; elas são contadas em separado.
- **Episódios censurados** (falha que não foi corrigida até o fim da janela) ficam fora da
  mediana, mas entram em `n_episodios` e `prop_censurados`.
- **Mês com mais de 1.000 runs** é dividido ao meio até caber no teto da API; se um único dia
  ainda passar de 1.000, o script avisa no log.

## Limites conhecidos

- A busca do GitHub devolve no máximo 1.000 resultados por consulta. Se uma faixa de estrelas
  tiver mais que isso, o script avisa no log e a faixa precisa ser fatiada no `config.yaml`.
- `compare` entre duas releases devolve no máximo 250 commits por página; o cliente segue a
  paginação, mas releases gigantes ficam caras em cota.
- `commit.author.date` é distorcido por rebase e squash merge, o que afeta o lead time.
- Release publicada não é deploy em produção, e falha de CI não é falha em produção: as duas
  métricas são proxies, e é isso que a validação manual e a análise de sensibilidade medem.
