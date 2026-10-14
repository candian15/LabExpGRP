# Dicionário de dados

Documenta todas as colunas dos CSVs que o pipeline escreve em `dados/`. É o
documento de referência para quem for replicar a coleta: sem ele não há como
comparar os valores obtidos com os nossos.

Gerado por `python -m pipeline --config config.yaml`. As definições operacionais
são as da seção 3 do enunciado; onde ele deixou a escolha para o grupo, a decisão
está registrada no [README](README.md#definições-operacionais-e-decisões-do-grupo).

**Convenções válidas para todos os campos:**

- **Janela de observação:** 12 meses, inclusiva nas duas pontas, definida em
  `config.yaml` (`janela.inicio`, `janela.fim`). Só entram releases publicadas e
  workflow runs criados dentro dela.
- **Branch:** só o *default branch* do repositório.
- **Datas:** UTC, formato ISO 8601.
- **Vazio:** significa **não medido**, e é diferente de `0`. Linhas com
  `motivo_descarte` preenchido têm todas as colunas de métrica vazias, porque o
  repositório saiu antes de ser medido.
- **Decimais:** arredondados em 4 casas.
- **Chave:** `repo` identifica a linha e não se repete.

---

## `dados/repositorios.csv`

Uma linha por repositório **avaliado** — os aprovados e os descartados. Quem foi
descartado tem `motivo_descarte` preenchido e as métricas vazias.

### Metadados

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `repo` | texto | — | `full_name` de `/search/repositories` (`owner/nome`) |
| `estrelas` | inteiro | estrelas | `stargazers_count` |
| `linguagem` | texto | — | `language`; vazio quando a API não define uma linguagem principal |
| `default_branch` | texto | — | `default_branch`; é o único branch considerado em todas as métricas |
| `criado_em` | data | ISO (UTC) | `created_at` |
| `idade_anos` | decimal | anos | `(janela.fim − created_at) / 365,25`. Medida até o **fim da janela**, não até a data da execução, para a coleta ser reproduzível |
| `contribuidores` | inteiro | pessoas | Nº da última página de `/contributors?per_page=1&anon=true`, lido no cabeçalho `Link`. Vazio quando `selecao.contribuidores: false` ou o endpoint deu 404 |

### Contagens da seleção

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `n_releases` | inteiro | releases | Releases publicadas na janela: `draft = false`, `prerelease = false`, `published_at` dentro da janela. É o numerador da RQ 01 e o critério de inclusão (≥ 5) |
| `n_runs_validos` | inteiro | runs | Workflow runs de `event = push` no default branch, criados na janela, cujo `conclusion` é de sucesso ou de falha. Critério de inclusão (≥ 50) |

`conclusion` é classificado assim (seção 3 do enunciado):

| `conclusion` | Tratamento |
|---|---|
| `success` | sucesso |
| `failure`, `timed_out`, `startup_failure` | falha |
| `cancelled`, `skipped`, `neutral`, `action_required`, `stale`, vazio | ignorado: não entra em cálculo nenhum |

### RQ 01 — deployment frequency

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `deployment_frequency` | decimal | releases/semana | `n_releases ÷ semanas da janela`, com `semanas = (fim − inicio + 1 dia) ÷ 7` (≈ 52,1 numa janela de 12 meses) |

### RQ 02 — lead time for changes (duas variantes obrigatórias)

Os commits de uma release R vêm de `compare/{release anterior}...{R}`; a data de
cada commit é `commit.author.date`. A release anterior pode estar fora da janela.
A primeira release da história do repositório não tem lead time.

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `lead_time_a_horas` | decimal | horas | **Variante (a), por release:** mediana, entre as releases do repositório, de `published_at(R) − data do commit mais antigo de R` |
| `lead_time_b_horas` | decimal | horas | **Variante (b), por commit:** mediana de `published_at(R) − data do commit`, sobre **todos** os commits de **todas** as releases |
| `releases_404` | inteiro | releases | Releases ignoradas no lead time porque o `compare` devolveu 404 (tag apagada ou reescrita) |

As duas variantes divergem porque um único commit antigo esquecido numa release
faz a (a) explodir e quase não move a (b).

### RQ 03 — change failure rate (duas variantes obrigatórias)

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `cfr_ci` | decimal | fração 0–1 | **Variante (a), proxy de CI:** `falhas ÷ (falhas + sucessos)` sobre os runs válidos, com todos os workflows juntos. Mede falha de *pipeline*, não falha em produção |
| `cfr_entrega` | decimal | fração 0–1 | **Variante (b), proxy de entrega:** `cfrb_releases_falha ÷ cfrb_releases_avaliadas`. Vazio quando nenhuma release pôde ser avaliada |
| `cfrb_releases_avaliadas` | inteiro | releases | Denominador do CFR (b): releases da janela que **não** caem na censura |
| `cfrb_releases_falha` | inteiro | releases | Releases seguidas, em até **7 dias**, por uma release corretiva |
| `cfrb_releases_censuradas` | inteiro | releases | Releases publicadas nos **últimos 7 dias da janela**: ainda não se sabe se haverá correção, então ficam fora do denominador |
| `cfrb_releases_corretivas` | inteiro | releases | Releases que a heurística marcou como corretivas (base da *rework rate*, RQ 08) |
| `cfrb_heuristica` | texto | — | Versão da heurística de release corretiva usada (`v1`, `v2`, `v3`), de `selecao.heuristica_cfrb` no config |

**Heurística de release corretiva** (`metricas/cfr_entrega.py`): é automática e
**aproximada**, e por isso é validada contra a amostra-ouro rotulada à mão
(precisão/recall/F1 em `validacao/historico_heuristica.md`). As versões são:

| Versão | Regra |
|---|---|
| `v1` | só muda o *patch* do SemVer (`2.3.0 → 2.3.1`) **ou** algum commit tem `fix`/`hotfix`/`revert` no assunto |
| `v2` | só muda o *patch* **ou** pelo menos metade dos commits são correções |
| `v3` | (só muda o *patch* **e** algum commit é correção) **ou** pelo menos metade dos commits são correções |

### RQ 04 — tempo de recuperação

Um **episódio de falha** é calculado **dentro de cada workflow**: começa na
primeira falha após um sucesso e termina no próximo sucesso daquele workflow.

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `recuperacao_horas` | decimal | horas | Mediana dos episódios concluídos: `updated_at(sucesso) − run_started_at(primeira falha)` |
| `n_episodios` | inteiro | episódios | Episódios encontrados, concluídos **e** censurados |
| `prop_censurados` | decimal | fração 0–1 | `episódios censurados ÷ n_episodios`. Censurado = a falha não foi corrigida até o fim da janela; fica fora da mediana, mas é reportado |

### Classificação DORA

Notas: **4 = Elite, 3 = High, 2 = Medium, 1 = Low**, pelos cortes fixos da
disciplina. A categoria geral é a **mediana** das quatro notas, arredondada para
baixo (exemplo do enunciado: 4, 3, 3, 1 → mediana 3 → High).

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `nota_frequencia` | inteiro | 1–4 | ≥ 7/sem = 4; ≥ 1 e < 7/sem = 3; ≥ 1/mês e < 1/sem = 2; < 1/mês = 1 |
| `nota_lead_time` | inteiro | 1–4 | < 24 h = 4; < 168 h = 3; < 720 h = 2; ≥ 720 h = 1. Calculada sobre `lead_time_a_horas` |
| `nota_cfr` | inteiro | 1–4 | ≤ 0,15 = 4; ≤ 0,30 = 3; ≤ 0,45 = 2; > 0,45 = 1. Calculada sobre `cfr_ci` |
| `nota_recuperacao` | inteiro | 1–4 | < 1 h = 4; < 24 h = 3; < 168 h = 2; ≥ 168 h = 1 |
| `dora_nota` | inteiro | 1–4 | Mediana das notas disponíveis, arredondada para baixo |
| `dora` | texto | — | `Elite`, `High`, `Medium` ou `Low`, conforme `dora_nota` |

Dois detalhes que mudam o resultado e precisam ser os mesmos na replicação:

- O corte **"1 por mês"** da frequência é convertido para releases/semana por mês
  médio de 365,25/12 dias (≈ 0,23/semana). Convertendo por "52,1 semanas ÷ 12",
  12 releases num ano cairiam em Low em vez de Medium.
- Métrica **vazia não recebe nota** e fica fora da mediana. Um repositório sem
  nenhuma release comparável ainda é classificado pelas outras três.

As colunas de nota usam a **combinação de referência C1** da RQ 07: release como
unidade de deploy, lead time (a) e CFR (a). As variantes (b) estão no CSV para a
análise de sensibilidade montar as outras combinações sem recoletar nada.

### Resultado da seleção

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `motivo_descarte` | texto | — | Vazio = entrou na amostra final. Valores: `sem_actions`, `poucas_releases`, `poucos_runs`, `erro` |

Os filtros são aplicados em ordem e param no primeiro que falha, então cada
repositório tem **um** motivo:

| Valor | Significado |
|---|---|
| `sem_actions` | `total_count = 0` em `/actions/workflows`: não usa GitHub Actions |
| `poucas_releases` | Menos de `selecao.min_releases` (5) releases publicadas na janela |
| `poucos_runs` | Menos de `selecao.min_runs` (50) runs válidos de `push` no default branch |
| `erro` | Erro definitivo da API depois das tentativas com backoff (ver o log da coleta) |

---

## `dados/funil.csv`

Quantos repositórios sobraram em cada etapa da seleção. Uma linha por etapa, na
ordem em que os filtros são aplicados. É a tabela do funil da seção de
Metodologia do artigo.

| Coluna | Tipo | Unidade | Origem / fórmula |
|---|---|---|---|
| `etapa` | texto | — | Critério da etapa. A primeira linha é o total de candidatos da busca e a última é a amostra final |
| `restantes` | inteiro | repositórios | Quantos ainda estavam na amostra depois da etapa |
| `descartados` | inteiro | repositórios | Quantos a etapa descartou. Vazio nas duas linhas de resumo, que não descartam nada |
| `motivo_do_descarte` | texto | — | Por que os descartados daquela etapa saíram |

A etapa **`avaliados`** aparece quando a busca devolveu mais candidatos do que
foram avaliados: a coleta para ao fechar `selecao.max_repositorios` aprovados, e
os candidatos restantes nunca foram consultados. Eles não são descarte por
critério, e é por isso que ficam numa etapa própria em vez de desaparecer da conta.

---

## Reproduzir os números

Os valores dependem de três coisas que precisam ser iguais:

1. **A janela** (`janela.inicio`/`janela.fim`), porque tudo é filtrado por ela.
2. **A versão da heurística** (`selecao.heuristica_cfrb`), que muda só o CFR (b).
3. **A data da coleta**, que não está sob controle: os repositórios continuam
   recebendo commits, releases e runs. Releases publicadas depois da nossa coleta
   mudam `n_releases` e, com ele, a frequência e as notas.

Por isso espera-se diferença relativa pequena em uma replicação, e não igualdade
exata. A classificação DORA é mais estável que os valores brutos, porque os
cortes são largos.
