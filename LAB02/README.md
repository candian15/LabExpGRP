# LAB02: assistentes de IA vs. codificação manual (experimento controlado)

Experimento *crossover within-subject*: cada integrante resolve metade dos katas com assistente de IA e metade sem, em ordem contrabalanceada, com time-box de 35 min por trial.

## Ambiente fixado

Para o tratamento ser comparável, todos os integrantes usam a mesma configuração em todos os trials:

| Item | Valor fixado |
|---|---|
| Linguagem | Python 3.12 |
| Testes de aceitação | pytest 8.3.3 |
| Assistente de IA (tratamento `ia`) | Claude (versão gratuita, claude.ai), sem autocomplete de IA na IDE |
| IDE | VS Code, com Copilot/autocomplete de IA desativado (inclusive nos trials `ia`, para o único canal de IA ser o chat) |
| Complexidade / MI / LOC | Radon 6.0.1 (`cc`, `mi`, `raw`) |
| Duplicação | jscpd (Node), `--min-tokens 30` |

O padrão do jscpd (50 tokens) é alto demais para katas curtos e faz toda medição dar 0%, por isso fixamos 30. Esse valor tem que ser o mesmo em todos os trials.

## Setup

```bash
cd LAB02
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
npm install -g jscpd                              # opcional: metrics.py também chama via npx
```

## Scripts

| Script | Para quê | Saída |
|---|---|---|
| [timer.py](timer.py) | Cronometra o trial (time-to-green ou censura em 35 min), para a RQ1 | `trials.csv` |
| [run_tests.py](run_tests.py) | Roda o pytest no código final e calcula a taxa de sucesso, para a RQ2 | `tests.csv` |
| [metrics.py](metrics.py) | Complexidade ciclomática, MI, LOC e % duplicação, para a RQ3 | `metrics.csv` |
| [dashboard.py](dashboard.py) | Consolida os três CSVs e gera os gráficos IA vs. manual (S03) | `graficos/*.png` |

## Fluxo de um trial

```bash
# 1. Durante o trial: cronômetro (encerra sozinho em 35 min)
python timer.py --integrante joao --kata kata01 --tratamento ia \
    --auto --test-path katas/kata01 --csv trials.csv

# 2. Depois do trial: testes de aceitação sobre o código final
python run_tests.py --integrante joao --kata kata01 --tratamento ia \
    --test-path katas/kata01 --total-esperado 8 --csv tests.csv

# 3. Depois do trial: métricas estáticas sobre a solução (sem os arquivos de teste)
python metrics.py --integrante joao --kata kata01 --tratamento ia \
    --src katas/kata01/solucao.py --csv metrics.csv
```

Use sempre `--csv` apontando para o mesmo arquivo em todos os trials. Os três CSVs se juntam depois por `(integrante, kata, tratamento)`, que é a chave de cada trial.

> `--src` do `metrics.py` deve apontar só para a solução. Incluir os arquivos de teste (que são idênticos entre os tratamentos) infla a duplicação e distorce a RQ3.

> `--total-esperado` é o número de testes de aceitação do kata, e fixa o denominador da taxa de sucesso. Sem ele, um trial cuja solução nem importa (erro de sintaxe ao fim dos 35 min) faria o pytest parar na coleta, e a taxa sairia calculada sobre o número de erros em vez do número de testes. Passe sempre, com o valor do kata.

## Métricas escolhidas por RQ

| RQ | Métrica primária | Complementares |
|---|---|---|
| RQ1: tempo | `tempo_segundos` (time-to-green), mediana por tratamento; trial que estoura o time-box entra censurado em 2100 s | — |
| RQ2: defeitos | `taxa_sucesso` (% de testes passando ao final) | `testes_falhando` (nº absoluto) |
| RQ3: estrutura | `complexidade_media` (McCabe por função) e `duplicacao_pct` | `loc`/`sloc` (controle, obrigatória) e `mi_medio` (Índice de Manutenibilidade) |

Dado o N pequeno (4 a 6 trials por integrante), as tabelas usam mediana e IQR, e a análise inferencial da S03 usa Wilcoxon pareado (desenho within-subject).

## Esquema dos CSVs

```
trials.csv   integrante, kata, tratamento, tempo_segundos, censurado, timestamp
tests.csv    integrante, kata, tratamento, testes_total, testes_passando, testes_falhando, taxa_sucesso, timestamp
metrics.csv  integrante, kata, tratamento, arquivos, loc, sloc, complexidade_media, mi_medio, duplicacao_pct, timestamp
```

`tratamento` é sempre `ia` ou `manual`. Colunas de métrica ficam vazias quando a ferramenta não estava disponível (ex.: `duplicacao_pct` sem jscpd). Vazio significa "não medido", diferente de `0`.

## Pendências

- Escolha e validação dos 4 ou 6 katas (dificuldade comparável, baixa indexação). A pasta `katas/` ainda não existe.
- Ordem de contrabalanceamento por integrante.
- S03: análise estatística (Wilcoxon) e dashboard consolidando `trials.csv` + `tests.csv` + `metrics.csv`.
