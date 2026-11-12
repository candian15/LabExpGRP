# LAB04 — Welch × Mann-Whitney no tempo até o merge de PRs

Simulação de Monte Carlo comparando o **teste t de Welch** e o **Mann-Whitney** em dados
assimétricos com outliers, usando como cenário o tempo até o merge de *pull requests* com e
sem revisão automática de um bot.

- **Dashboard publicado:** https://candian15.github.io/LabExpGRP/
- **Repositório:** https://github.com/candian15/LabExpGRP
- **GitHub Projects:** https://github.com/users/candian15/projects/2

## Rodar

Tudo a partir desta pasta (`LAB04/`):

```bash
pip install -r requirements.txt
python -m src.rodar_tudo               # simulações, figuras e a página publicada
streamlit run dashboard/app.py         # abre o dashboard em http://localhost:8501
```

`python -m src.rodar_tudo` é o comando único do enunciado: ele roda todas as simulações,
grava os CSVs de `resultados/`, salva as quatro figuras em `docs/` e gera o
[`index.html`](../index.html) da raiz, que é a página servida pelo GitHub Pages. Cada
etapa é de um integrante; etapa cujo módulo ainda não está no repositório aparece como
`PENDENTE` e as outras continuam, então o comando funciona com a sprint pela metade.

O dashboard existe em duas formas, com o mesmo conteúdo: a **página publicada**, estática
e feita para apresentar em projetor, e o **Streamlit**, que roda localmente e desenha os
gráficos na hora.

Tudo usa a semente registrada em `config/cenario.yaml`, então **duas execuções produzem
exatamente os mesmos arquivos**. O dashboard lê esses CSVs e gera os gráficos na hora.

Para rodar as partes isoladamente:

```bash
python -m src.simulacao     # gera um conjunto simulado e imprime as medianas
python -m src.testes        # aplica Welch e Mann-Whitney a esse conjunto
python -m src.monte_carlo   # Q1 e Q2: 10.000 repetições, grava resultados/q1.csv e q2.csv
python -m src.q3            # Q3: as situações que violam os pressupostos
python -m src.dados_reais   # aplica os dois testes aos 60 PRs reais
python -m src.resultados    # mostra o que já existe em resultados/
python -m src.graficos      # salva o G2, o G3 e o G4 em docs/
python -m src.graficos_g1   # salva o G1 em docs/
python -m src.gerar_pagina  # gera o index.html publicado no GitHub Pages
```

## Testes

```bash
pytest -q
```

São 90 testes. O CI do GitHub Actions
([`testes-lab04.yml`](../.github/workflows/testes-lab04.yml)) roda a suíte, executa
`python -m src.rodar_tudo` e executa o script do dashboard de ponta a ponta — o Streamlit
só desenha com um servidor, e é nessa execução que um erro de import ou de dado apareceria.

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
| `src/monte_carlo.py` | Repete a simulação 10.000 vezes e conta as rejeições (Q1 e Q2) |
| `src/q3.py` | Repete a Q1 e a Q2 nas situações que violam os pressupostos (Q3) |
| `src/dados_reais.py` | Aplica os dois testes aos 60 PRs coletados |
| `src/resultados.py` | Lê os CSVs de `resultados/` e entrega a tabela que o G3 e o G4 usam |
| `src/graficos_g1.py` | `fig_g1`: dados reais × simulados |
| `src/graficos.py` | `fig_g2`: estatística sob H₀; `fig_g3`: erro tipo I; `fig_g4`: curvas de poder |
| `src/gerar_pagina.py` | Gera o `index.html` publicado, a partir dos CSVs e do cenário |
| `src/rodar_tudo.py` | O comando único: simulações, figuras e página publicada |
| `resultados/q1.csv` | Erro tipo I no cenário real (Q1) |
| `resultados/q2.csv` | Poder nas cinco razões de medianas (Q2) |
| `resultados/q3.csv` | Erro tipo I e poder nas situações que violam os pressupostos (Q3) |
| `resultados/dados_reais.csv` | Os dois testes aplicados aos 60 PRs coletados |
| `docs/g1…g4*.png` | As quatro figuras, geradas pelo comando único |
| `../index.html` | A página do GitHub Pages, gerada por `src/gerar_pagina.py` |
| `dashboard/app.py` | Dashboard em Streamlit com as sete seções do enunciado |
| `docs/cenario.md` | Pergunta, hipóteses, método da simulação e o que o grupo esperava |
| `docs/interpretacao_s01.md` | O que cada teste concluiu no conjunto simulado |
| `docs/interpretacao_q3_dados_reais.md` | Leitura da Q3 e dos testes nos PRs reais |
| `tests/` | `pytest` |

## O cenário, em uma frase

O tempo até o merge de um PR é diferente quando ele recebe a revisão de um bot? **H₀:** os
dois grupos têm a mesma distribuição. **H₁:** o tempo é diferente. Teste bicaudal, α = 0,05.

O detalhe completo — incluindo o que o grupo esperava **antes** de simular — está em
[`docs/cenario.md`](docs/cenario.md).

## Divisão

| Integrante | S01 | S02 | Entrega final |
|---|---|---|---|
| Arthur | Coleta dos dados reais, parâmetros da simulação, cenário e G1 | Q3 (violação dos pressupostos) e os testes nos dados reais | Apresenta as perguntas 3, 4, 11 e 14 |
| Pedro | Gerador de dados simulados, os dois testes, interpretação e G2 | Motor de Monte Carlo, Q1 e Q2 | Seções 4, 5 e 7; perguntas 8, 9, 10, 12, 13 e 15 |
| João (Santana) | Dashboard, seções da S01, README e execução, testes e CI | G3, G4, seções 4 e 5 do dashboard e o comando único | Página publicada, seções 6 e 7, perguntas 1, 2, 5, 6 e 7 |
