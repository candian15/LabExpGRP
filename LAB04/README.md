# LAB04 — Welch × Mann-Whitney no tempo até o merge de PRs

Simulação de Monte Carlo comparando o **teste t de Welch** e o **Mann-Whitney** em dados
assimétricos com outliers, usando como cenário o tempo até o merge de *pull requests* com e
sem revisão automática de um bot.

- **Repositório:** https://github.com/candian15/LabExpGRP
- **GitHub Projects:** https://github.com/users/candian15/projects/2

## Rodar

Tudo a partir desta pasta (`LAB04/`):

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

O dashboard abre em `http://localhost:8501` com as três seções da S01. Ele gera os números
na hora, a partir de `config/cenario.yaml` e da semente registrada nele, então **duas
execuções dão exatamente o mesmo resultado**.

Para rodar as partes isoladamente:

```bash
python -m src.simulacao    # gera um conjunto simulado e imprime as medianas
python -m src.testes       # aplica Welch e Mann-Whitney a esse conjunto
python -m src.graficos     # salva figs/g2.png
python -m src.graficos_g1  # salva o G1 em docs/
```

## Testes

```bash
pytest -q
```

São 27 testes. O CI do GitHub Actions
([`testes-lab04.yml`](../.github/workflows/testes-lab04.yml)) roda a suíte e, além disso,
executa o script do dashboard de ponta a ponta — o Streamlit só desenha com um servidor, e
é nessa execução que um erro de import ou de dado apareceria.

## Estrutura

| Caminho | O que é |
|---|---|
| `config/cenario.yaml` | Parâmetros da simulação: distribuição, μ, σ e mediana de cada grupo, semente e tamanho da amostra |
| `data/dados_reais.csv` | 30 PRs por grupo coletados da API do GitHub |
| `data/FONTE.md` | Repositório, bot, janela de coleta e método |
| `data/estatisticas_descritivas.csv` | Mediana, IQR, assimetria e outliers por grupo |
| `src/coletar_dados_reais.py` | Coleta os PRs reais |
| `src/parametros_reais.py` | Ajusta a lognormal aos dados reais e grava o `cenario.yaml` |
| `src/simulacao.py` | Gera os grupos simulados com semente fixa |
| `src/testes.py` | Aplica Welch e Mann-Whitney, com tamanho do efeito |
| `src/graficos_g1.py` | `fig_g1`: dados reais × simulados |
| `src/graficos.py` | `fig_g2`: distribuição da estatística sob H₀ |
| `dashboard/app.py` | Dashboard em Streamlit com as seções da S01 |
| `docs/cenario.md` | Pergunta, hipóteses, método da simulação e o que o grupo esperava |
| `docs/interpretacao_s01.md` | O que cada teste concluiu no conjunto simulado |
| `tests/` | `pytest` |

## O cenário, em uma frase

O tempo até o merge de um PR é diferente quando ele recebe a revisão de um bot? **H₀:** os
dois grupos têm a mesma distribuição. **H₁:** o tempo é diferente. Teste bicaudal, α = 0,05.

O detalhe completo — incluindo o que o grupo esperava **antes** de simular — está em
[`docs/cenario.md`](docs/cenario.md).

## Divisão da S01

| Integrante | Entrega |
|---|---|
| Arthur | Coleta dos dados reais, parâmetros da simulação, cenário e G1 |
| Pedro | Gerador de dados simulados, os dois testes, interpretação e G2 |
| João | Dashboard, seções da S01, README e execução, testes e CI |
