# Q3 e testes nos dados reais: o que os números mostram

Resultados de `python -m src.q3` (10.000 repetições por célula, semente 42) e de
`python -m src.dados_reais`. Os números estão em `resultados/q3.csv` e
`resultados/dados_reais.csv`. Margem de erro das taxas: cerca de ±0,4 ponto percentual.

## Q3: as três situações

| Situação | O que muda em relação ao cenário real |
|---|---|
| bem comportada | σ = 0,3 (dados quase simétricos), n = 30 |
| amostra pequena | σ real (2,42), n = 10 |
| com outliers | σ = 0,3, n = 30, cada valor com 10% de chance de ser multiplicado por 10 |

**Erro tipo I (razão = 1, esperado ≈ 5%)**

| Situação | Welch | Mann-Whitney |
|---|---|---|
| cenário real (Q1) | 1,49% | 4,74% |
| bem comportada | 4,80% | 4,54% |
| amostra pequena | 0,81% | 4,66% |
| com outliers | 4,06% | 5,09% |

**Poder para uma razão de medianas de 0,6 (efeito moderado)**

| Situação | Welch | Mann-Whitney |
|---|---|---|
| bem comportada | 100% | 100% |
| amostra pequena | 0,9% | 6,4% |
| com outliers | 19,1% | 99,7% |

Leitura:

- **Nenhum teste fica liberal.** Quando se afastam de 5%, os dois ficam abaixo (conservadores): o Welch é o que mais se afasta, principalmente nos dados muito assimétricos (1,5% no cenário real e 0,8% com n = 10).
- **Com dados bem comportados os testes empatam.** O Welch tem um pouco mais de poder em um efeito pequeno (78,9% contra 78,1% para razão 0,8), como se espera quando o pressuposto vale.
- **A vantagem do Mann-Whitney vem das violações.** Com outliers, ele detecta o efeito de razão 0,6 em 99,7% das repetições, e o Welch em 19,1%. Com n = 10 e dados assimétricos, nenhum dos dois tem poder útil, mas o Mann-Whitney sai na frente.
- **O Welch com n = 10 e cauda pesada chega a ter poder abaixo do nível.** Para razão 0,2 ele rejeita só em 3,6% das repetições, menos que os 5% de H₀ verdadeira. Os outliers inflam o erro padrão mais do que a diferença entre as médias.

## Testes nos 60 PRs reais

| Teste | Estatística | p-valor | Efeito | Conclusão a 5% |
|---|---|---|---|---|
| Welch | 1,387 | 0,174 | d de Cohen = +0,36 (pequeno) | não rejeita H₀ |
| Mann-Whitney | 646 | 0,004 | delta de Cliff = +0,44 (médio) | rejeita H₀ |

Os dois testes **chegaram a conclusões diferentes**. É o que a simulação previa para dados deste tipo: com a cauda longa dos tempos de merge (assimetria 4,4 e 4,0), a média é arrastada por poucos PRs muito lentos, e o Welch perde poder. O sinal positivo do efeito quer dizer que os PRs sem bot demoram mais (mediana de 7,7 h contra 1,5 h). Isso não prova que o bot causa a diferença, porque os PRs não foram sorteados entre as duas condições.

## O que o grupo esperava × o que apareceu (para a pergunta 13)

- **Mann-Whitney com mais poder:** confirmado, e com folga em todas as situações com assimetria ou outliers.
- **Os dois testes perto de 5% sem efeito:** confirmado só para o Mann-Whitney. O Welch ficou bem abaixo nos dados assimétricos (1,5% e 0,8%), mais conservador do que o esperado.
- **A vantagem some quando os dados são bem comportados:** confirmado (os dois empatam).

## Texto sugerido para o dashboard

**Seção 6 (dados reais):** "Nos 60 PRs, o Welch não rejeita H₀ (p = 0,174; d = +0,36, efeito pequeno) e o Mann-Whitney rejeita (p = 0,004; delta de Cliff = +0,44, efeito médio). Os testes discordam porque o Welch compara médias e os tempos de merge têm cauda muito longa, o que o deixa pouco sensível, como a simulação mostrou. A diferença entre as medianas (7,7 h sem bot e 1,5 h com bot) é grande na prática, mas não prova que o bot causa o menor tempo, já que ele não foi atribuído aleatoriamente aos PRs."
