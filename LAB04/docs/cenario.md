# Cenário: tempo até o merge de PRs com e sem bot de revisão

**Par de testes (P1):** t de Welch × Mann-Whitney.

## Pergunta

O tempo até o merge de um PR é diferente quando ele recebe a revisão automática de um bot?

## Hipóteses

- **H₀:** os PRs com e sem bot de revisão têm o mesmo tempo até o merge (mesma distribuição; em particular, médias iguais para o Welch e P(X > Y) = 0,5 para o Mann-Whitney).
- **H₁:** o tempo até o merge é diferente entre os dois grupos.

**Teste bicaudal**, com α = 0,05. Não há razão forte para fixar a direção: o bot pode acelerar o merge (feedback imediato) ou atrasá-lo (mais comentários e mais rodadas de correção), e os dois resultados interessam ao projeto.

## Dados reais (de onde vieram os parâmetros)

Fonte: `ant-design/ant-design`, bot `copilot-pull-request-reviewer`, PRs criados de 2026-07-01 a 2026-10-31 (detalhes em `data/FONTE.md`). 30 PRs por grupo, tempo em horas.

| Grupo | n | Mediana | Q1–Q3 | Assimetria | Outliers (Tukey) | Máximo |
|---|---|---|---|---|---|---|
| sem bot | 30 | 7,7 h | 1,5–41,8 h | 4,4 | 5 | 1.179 h |
| com bot | 30 | 1,5 h | 0,4–3,0 h | 4,0 | 5 | 333 h |

Os dois grupos são **muito assimétricos e têm outliers**: a média (81 h e 21 h) fica muito acima da mediana. O teste de Shapiro-Wilk rejeita normalidade nos dados brutos dos dois grupos (p < 0,001); em escala log o grupo sem bot é compatível com normal (p = 0,91) e o grupo com bot se afasta um pouco (p = 0,011). A razão entre as medianas observada é de cerca de 0,19.

## Como os dados simulados serão gerados

- **Distribuição:** lognormal em cada grupo, porque o tempo é positivo, assimétrico e tem cauda longa; o ajuste em escala log é razoável nos dados reais.
- **Parâmetros (de `config/cenario.yaml`):**
  - sem bot (controle): μ = 2,118 e σ = 2,421, ou seja, mediana ≈ 8,3 h;
  - com bot (tratamento observado): μ = 0,444 e σ = 1,997, ou seja, mediana ≈ 1,6 h.
- **Tamanho da amostra:** 30 por grupo, como nos dados reais.
- **Efeito nas simulações de Q1 a Q3:** razão entre as medianas (tratamento ÷ controle). O controle usa os parâmetros reais; o tratamento usa `μ = μ_controle + ln(razão)` e o mesmo σ. Razão = 1,0 é H₀ verdadeira; os valores previstos são 1,0; 0,8; 0,6; 0,4 e 0,2 (este último é quase o que se observou).
- **Repetições:** 10.000 conjuntos por situação, com `numpy.random.default_rng(42)`.
- **Situações para a Q3 (violação dos pressupostos):** além do caso real (σ ≈ 2,4, muito assimétrico), uma situação "bem comportada" (σ pequeno, dados próximos de simétricos), amostras pequenas (n = 10) e com outliers contaminados.

## O que o grupo espera antes de simular

> Registrado **antes** de rodar as simulações das Q1 a Q3.

- **Erro tipo I (Q1):** com H₀ verdadeira os dois grupos têm a mesma distribuição, então esperamos que **os dois testes fiquem perto de 5%**. O Welch pode ficar um pouco abaixo ou acima por causa da assimetria extrema, já que a média de uma lognormal com σ ≈ 2,4 é dominada por poucos valores enormes.
- **Poder (Q2):** esperamos que o **Mann-Whitney detecte melhor o efeito** do que o Welch. O Welch compara médias, e a variância enorme causada pelos outliers mascara a diferença; o Mann-Whitney compara postos e quase não sofre com valores extremos.
- **Quando a vantagem muda (Q3):** esperamos que a vantagem do Mann-Whitney **diminua ou desapareça** quando os dados forem simétricos e bem comportados, situação em que o Welch costuma ser um pouco mais poderoso.

## Erro tipo I e tipo II neste cenário (para a apresentação)

- **Erro tipo I:** concluir que o bot muda o tempo de merge quando na verdade não muda. Consequência: o projeto adota ou mantém uma ferramenta sem benefício real.
- **Erro tipo II:** não detectar um efeito real do bot. Consequência: o projeto abandona ou não adota uma ferramenta que ajudaria.
- Para um projeto que está decidindo se adota o bot, o erro tipo I tende a ser o mais caro (custo de configuração e de revisão extra sem retorno), mas a resposta depende do custo do bot no projeto.

## Texto sugerido para o dashboard

**Seção 1 (Cenário):** "Queremos saber se o tempo até o merge de PRs muda quando eles recebem a revisão de um bot. H₀: não muda; H₁: muda (teste bicaudal). Coletamos 30 PRs com bot e 30 sem bot do repositório ant-design/ant-design (PRs criados entre jul. e out. de 2026), pela API do GitHub."

**Seção 2 (Os dados):** "Os tempos de merge são muito assimétricos: a mediana é de 7,7 h sem bot e 1,5 h com bot, mas há PRs que levaram mais de 300 h. Por isso simulamos os dois grupos com distribuições lognormais cujos parâmetros foram ajustados aos dados reais (σ ≈ 2,4 e 2,0 na escala log). O eixo está em escala log para que a forma de cada grupo apareça."
