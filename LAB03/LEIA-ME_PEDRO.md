# Parte do Pedro — Lab03 Sprint 1

O pacote traz quatro coisas:
- o cliente da API (cache, paginação, rate limit e backoff) que o grupo inteiro usa;
- a coleta de workflow runs;
- as métricas CFR (a) e tempo de recuperação;
- os testes, o CI e as hipóteses das RQ 03 a 05.

## Arquivos

| Arquivo | O que é |
|---|---|
| `pipeline/github_client.py` | Cliente HTTP compartilhado (base do Artur e do João) |
| `pipeline/coleta_runs.py` | Runs de `push` no default branch, janela dividida por mês |
| `metricas/cfr.py` | Classificação de `conclusion` e CFR (a) |
| `metricas/recuperacao.py` | Episódios de falha, censura e mediana em horas (RQ 04) |
| `tests/` | 53 testes; métricas com 99–100% de cobertura |
| `.github/workflows/testes.yml` | CI rodando pytest com `--cov-fail-under=80` |
| `requirements.txt`, `pytest.ini`, `.gitignore` | Configuração básica (o `.gitignore` já exclui `cache/` e `.env`) |
| `docs/hipoteses_rq3_rq5.md` / `.tex` | Texto da Introdução para o João juntar |

## Como rodar

```bash
pip install -r requirements.txt
pytest --cov=metricas --cov-report=term-missing

# testar a coleta com um repositório (Linux/macOS; no PowerShell: $env:GITHUB_TOKEN="ghp_...")
export GITHUB_TOKEN=ghp_...
python -m pipeline.coleta_runs psf/requests --inicio AAAA-MM-DD --fim AAAA-MM-DD
```

Troque as datas pelas da janela que o professor fixou. O comando salva `dados/runs/psf__requests.csv` e imprime o CFR (a), o tempo de recuperação e quantas chamadas vieram do cache. Se você rodar de novo, tudo vem do cache e nenhuma cota é gasta.

## Para o Artur e o João usarem

```python
from pipeline.github_client import GitHubClient, NaoEncontrado

gh = GitHubClient()                                   # lê GITHUB_TOKEN
gh.get("/repos/o/r")                                  # um objeto (com cache)
gh.listar("/repos/o/r/releases")                      # todas as páginas numa lista
gh.listar("/repos/o/r/compare/v1...v2")               # junta os "commits" de todas as páginas
gh.contar_por_link("/repos/o/r/contributors", {"anon": "true"})  # nº de contribuidores
```

- **Artur:**
  - um `compare` com tag apagada levanta `NaoEncontrado`; é só capturar, contar e pular a release;
  - o 404 também fica no cache, então não é repetido.
- **João:**
  - `repo_usa_actions(gh, o, r)` faz o descarte de quem não usa Actions;
  - `len(runs_validos(runs)) >= 50` faz o filtro de inclusão;
  - na classificação DORA, `cfr_ci` devolve uma **fração de 0 a 1** (Elite é ≤ 0.15) e o tempo de recuperação vem em **horas** (Elite é < 1).

O `config.yaml` com as datas da janela fica com o João. A coleta recebe `inicio` e `fim` como `date`.

## Decisões que precisam ir para o artigo

- **Falhas antes do primeiro sucesso de um workflow** na janela não abrem episódio, porque o enunciado define o início do episódio como "primeira falha após um sucesso". Elas são contadas em `falhas_sem_sucesso_anterior`.
- **Episódios censurados** ficam fora da mediana, mas entram em `n_censurados` e `prop_censurados`.
- **Mês com mais de 1.000 runs** é dividido ao meio até caber no teto da API. Se um único dia ainda passar de 1.000, aparece um aviso no log, e isso deve ser registrado como ameaça à validade.
- **Re-runs** (`run_attempt > 1`): a API devolve só a conclusão da última tentativa.

## Issues e commits sugeridos

Criem as Issues no Projects antes e troquem `#N` pelo número real de cada uma.

1. `#N cliente HTTP com cache, paginação, rate limit e backoff`: `pipeline/github_client.py`, `tests/test_github_client.py`, `requirements.txt`, `pytest.ini`, `.gitignore`
2. `#N coleta de workflow runs com subdivisão mensal`: `pipeline/coleta_runs.py`, `tests/test_coleta_runs.py`
3. `#N CFR (a) e tempo de recuperação com testes`: `metricas/`, `tests/conftest.py`, `tests/test_cfr.py`, `tests/test_recuperacao.py`
4. `#N CI rodando testes`: `.github/workflows/testes.yml`
5. `#N hipóteses RQ3–RQ5`: `docs/`

Façam commits separados, um por Issue. Assim o histórico mostra a evolução e cada commit referencia a sua Issue.
