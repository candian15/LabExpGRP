# LAB01 — Características de repositórios populares + Setup do Kanban

Mineração das características dos 1.000 repositórios mais populares do GitHub (por estrelas), organizada por questão de pesquisa (RQ), não por sprint — o código de cada RQ evolui no lugar, sem pastas separadas por sprint.

## Questões de pesquisa

| RQ | Pergunta | Métrica | Onde está |
|---|---|---|---|
| RQ01 | Sistemas populares são maduros/antigos? | Idade do repositório | [RQ01_RQ02/](RQ01_RQ02/) |
| RQ02 | Recebem muita contribuição externa? | Total de PRs aceitas | [RQ01_RQ02/](RQ01_RQ02/) |
| RQ03 | Lançam releases com frequência? | Total de releases | [RQ03_RQ04/](RQ03_RQ04/) |
| RQ04 | São atualizados com frequência? | Tempo até a última atualização | [RQ03_RQ04/](RQ03_RQ04/) |
| RQ05 | São escritos nas linguagens mais populares? | Linguagem primária | [RQ05_RQ06/](RQ05_RQ06/) |
| RQ06 | Possuem alto percentual de issues fechadas? | Issues fechadas / total | [RQ05_RQ06/](RQ05_RQ06/) |
| RQ07 | Linguagens mais populares recebem mais contribuição/releases/atualizações? | RQ02+RQ03+RQ04 por linguagem | [RQ07/](RQ07/) |

## Como rodar tudo

Em vez de entrar em cada pasta e lembrar o script/flag/CSV certos, use [main.py](main.py):

```bash
pip install -r requirements.txt
export GITHUB_TOKEN="seu_token_aqui"   # só necessário para rodar extract

python main.py --list                              # status: o que já foi gerado, o que falta
python main.py --rq all --stage all --mode full     # pipeline completo: extract(1000) -> analyze -> visualize de cada RQ, depois merge+visualize da RQ07
python main.py --rq RQ01_RQ02 --stage extract --mode sample   # só uma RQ, só um estágio
```

`--rq` e `--stage` aceitam múltiplos valores ou `all`; `--mode` é `sample` (8) / `100` / `full` (1000). Detalhes em `python main.py --help`.

Ao rodar `extract` para várias RQs seguidas (`--rq all`), o `main.py` pausa alguns segundos entre uma extração e outra para não estourar o rate limit do GitHub — veja mais na seção abaixo.

## Pipeline de execução manual (por RQ)

Caso prefira rodar direto os scripts de cada RQ (o que `main.py` faz por baixo dos panos):

1. `extract.py --sample` — 8 repositórios, para validar manualmente os campos contra o GitHub antes de rodar em escala.
2. `extract.py` — 100 repositórios.
3. `extract.py --full` — 1000 repositórios, com paginação.
4. `analyze_*.py` (quando existir) — checa valores ausentes, distribuição e outliers (IQR) no dataset de 1000.
5. `visualize_*.py` — gera os gráficos.
6. Só depois de RQ01_RQ02, RQ03_RQ04 e RQ05_RQ06 terem o dataset de 1000 completo: rodar [RQ07/rq07_analysis.py](RQ07/rq07_analysis.py), que junta os três CSVs por linguagem, e então [RQ07/visualize_rq07.py](RQ07/visualize_rq07.py).

Critério de seleção dos repositórios em todas as RQs: `stars:>1000 sort:stars-desc` via GraphQL `search(type: REPOSITORY)`. Todas as extrações usam só a stdlib (`urllib`) para consultar a API do GitHub — sem bibliotecas de terceiros, conforme exigido pelo enunciado.

## Rate limit do GitHub

Os três scripts de extração fazem paginação da mesma busca (`stars:>1000 sort:stars-desc`) via GraphQL `search`, que tem um limite mais apertado que o limite geral da API (5000 pontos/hora) — o GitHub aplica um **rate limit secundário** (anti-abuso) para muitas requisições seguidas em pouco tempo, retornando erro 403/429. Isso acontecia porque o intervalo entre páginas era de só 0.5s, e rodar várias RQs em sequência multiplicava o problema.

Ajustes feitos:
- Intervalo entre páginas de cada extração: `0.5s` → `2s`.
- Retry com backoff exponencial (5s, 10s, 20s... até 120s) em erro 403/429/502/503/504, respeitando o header `Retry-After` quando o GitHub manda — antes só o script de RQ03_RQ04 tinha retry, e mesmo esse não cobria rate limit (só erro de servidor).
- `main.py` pausa 10s entre a extração de uma RQ e a próxima quando roda `--rq all`.

Se mesmo assim continuar batendo rate limit: espere alguns minutos antes de rodar de novo (o header `resetAt`, impresso a cada página, mostra quando o limite primário reseta), ou rode uma RQ de cada vez em vez de `--rq all`.

## Pendências conhecidas

- **CSV de 1000 repositórios de RQ05_RQ06 ainda falta:** [`RQ01_RQ02/rq01_rq02_1000.csv`](RQ01_RQ02/rq01_rq02_1000.csv) e [`RQ03_RQ04/rq03_rq04_1000.csv`](RQ03_RQ04/rq03_rq04_1000.csv) já estão commitados; falta rodar `python main.py --rq RQ05_RQ06 --stage extract --mode full` e commitar o `rq05_rq06_1000.csv` resultante — só depois disso dá pra rodar o merge da RQ07 (`python main.py --rq RQ07 --stage merge`).
- **Relatório final:** ainda não existe o documento com introdução (hipóteses informais), metodologia, resultados por RQ, discussão hipótese vs. resultado, e a seção "Configuração do processo" (estrutura do GitHub Projects, política de WIP, print do board).
- **GitHub Projects (v2):** setup do board, Issues rastreáveis, referência ao número da Issue em cada commit, snapshot CSV de fechamento de sprint — isso não é verificável por código, precisa ser conferido direto no GitHub.
- Link do repositório/GitHub Projects do grupo ainda precisa ser preenchido no relatório final.
