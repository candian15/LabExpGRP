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

A coleta completa demora **horas** e bate no rate limit várias vezes (o script espera sozinho
e continua). O gargalo não é a cota, e sim a latência: as chamadas são sequenciais, e um
repositório muito ativo precisa de uma consulta por mês da janela, cada uma paginada. Para
testar, baixe `max_repositorios` para 2 ou 3 antes de rodar a amostra inteira.

Para deixar rodando e acompanhar o progresso, use `python -u` (sem o `-u`, a saída fica presa
no buffer quando é redirecionada para arquivo):

```bash
mkdir -p cache
nohup setsid python -u -m pipeline --config config.yaml > cache/coleta.log 2>&1 &
tail -f cache/coleta.log
```

O log traz uma linha por repositório aprovado e uma linha de progresso a cada 25 candidatos
avaliados. Se a coleta cair, o mesmo comando continua de onde parou.

### config.yaml

| Chave | O que faz |
|---|---|
| `janela.inicio` / `janela.fim` | Janela de observação (12 meses, datas fixadas pelo professor). Inclusiva nas duas pontas |
| `busca.faixas_estrelas` | Faixas de `stars:` consultadas. A busca devolve no máximo 1.000 resultados por consulta, então faixas largas precisam ser fatiadas |
| `busca.linguagens` | Vazio = todas. Preencher fatia a busca ainda mais (`language:`) |
| `selecao.min_releases` / `min_runs` | Critério mínimo de inclusão (5 releases e 50 runs válidos na janela) |
| `selecao.max_repositorios` | Para a coleta ao fechar essa quantidade de repositórios aprovados |
| `selecao.contribuidores` | Conta contribuidores dos aprovados (1 chamada extra cada), para os quartis da RQ 06 |
| `selecao.heuristica_cfrb` | Versão da heurística de release corretiva usada no CFR (b): `v1`, `v2` ou `v3` |
| `cache` / `saida` | Pastas do cache da API e dos CSVs |

## Saídas

`dados/funil.csv` — quantos repositórios sobraram em cada etapa da seleção e o motivo de
cada descarte (tabela da seção de Metodologia do artigo).

`dados/repositorios.csv` — uma linha por repositório **avaliado** (os descartados ficam na
tabela, com as métricas em branco e o motivo preenchido).

### Dicionário de dados

Todas as colunas dos dois CSVs — nome, tipo, unidade e fórmula ou origem na API —
estão em [DICIONARIO_DADOS.md](DICIONARIO_DADOS.md), junto com os cortes da
classificação DORA e o que precisa ser igual para reproduzir os números.

As métricas com variante obrigatória aparecem nas duas: lead time (a) por release
e (b) por commit, CFR (a) proxy de CI e (b) proxy de entrega. A classificação usa
a combinação de referência **C1** da RQ 07 (release como deploy, lead time (a),
CFR (a)); as variantes (b) ficam no CSV para a análise de sensibilidade.

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
| [metricas/cfr.py](metricas/cfr.py) | Change failure rate, variante (a), proxy de CI (RQ 03) |
| [metricas/cfr_entrega.py](metricas/cfr_entrega.py) | Change failure rate, variante (b), proxy de entrega (RQ 03) |
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
- **A amostra não é aleatória**, e isso é uma ameaça à validade externa. As faixas de estrelas
  do `config.yaml` têm, cada uma, muito mais repositórios que o teto de 1.000 da busca (a faixa
  `1000..1500` sozinha tem mais de 20 mil), então entram os **1.000 mais estrelados de cada
  faixa**, e não um sorteio dela. Fatiar em faixas estreitas reduz o efeito, mas não o elimina:
  dentro de qualquer faixa com mais de 1.000 repositórios, os menos estrelados nunca são vistos.
  A amostra é lida como "repositórios populares que usam Actions", não como "repositórios com
  mais de 1.000 estrelas".
- **O `total_count` de `/actions/runs` satura em 2.500.** Um mês e a sua primeira metade podem
  devolver os mesmos 2.500, então esse número não serve para saber quantos runs existem de
  verdade. Ele é usado só como gatilho da subdivisão da janela, nunca como medida.
- **Repositório com mais de 1.000 runs em um único dia é descartado** (`runs_acima_do_teto` no
  funil). A consulta devolve no máximo 1.000 resultados e não existe filtro mais fino que a
  data, então não há como obter os runs daquele dia. Incluir o repositório assim faria o
  CFR (a) e o tempo de recuperação serem calculados sobre um subconjunto truncado de tamanho
  desconhecido — e, como o `total_count` satura, nem daria para dizer o quanto falta. Um
  descarte contado no funil é uma limitação conhecida; um número calculado sobre dados
  truncados em silêncio é um erro invisível. O funil mostra quantos repositórios saíram por
  esse motivo, e isso vai para as ameaças à validade externa (a amostra exclui os projetos
  mais hiperativos).
- Repositórios muito ativos custam centenas de chamadas e muita memória. A coleta de runs
  resume cada página assim que ela chega, em vez de juntar todas antes, senão a recursão de
  subdivisão estoura a memória em máquinas com pouca RAM.
- `compare` entre duas releases devolve no máximo 250 commits por página; o cliente segue a
  paginação, mas releases gigantes ficam caras em cota.
- `commit.author.date` é distorcido por rebase e squash merge, o que afeta o lead time.
- Release publicada não é deploy em produção, e falha de CI não é falha em produção: as duas
  métricas são proxies, e é isso que a validação manual e a análise de sensibilidade medem.
