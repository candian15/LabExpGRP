# Desenho do Experimento — Lab02 (Passo 1)

## A) Hipóteses

### RQ1 — Tempo
- **H0₁**: não há diferença no tempo até passar em todos os testes de aceitação (time-to-green) entre resolver com assistente de IA e resolver manualmente.
- **H1₁**: o uso de assistente de IA reduz o tempo até passar em todos os testes de aceitação, em comparação à codificação manual.

### RQ2 — Defeitos
- **H0₂**: não há diferença na taxa de sucesso dos testes de aceitação ao final do time-box entre os dois tratamentos.
- **H1₂**: o uso de assistente de IA aumenta a taxa de sucesso dos testes de aceitação ao final do time-box, em comparação à codificação manual.

### RQ3 — Estrutura do código
- **H0₃**: não há diferença na complexidade ciclomática média e na duplicação de código entre os dois tratamentos.
- **H1₃**: o uso de assistente de IA altera (aumenta ou reduz) a complexidade ciclomática média e/ou a duplicação de código, em comparação à codificação manual.

## B) Variáveis dependentes

- Tempo até passar em todos os testes de aceitação ("time-to-green"), em minutos; trials que atingem o time-box (35 min) sem sucesso são registrados como censurados em 35 min (não descartados).
- Taxa de sucesso: % de testes de aceitação passando ao final do time-box.
- Número absoluto de testes falhando ao final do tempo.
- Complexidade ciclomática média por método/função (via ferramenta equivalente a Radon/CK, conforme linguagem escolhida pelo grupo).
- % de linhas duplicadas (via PMD CPD / jscpd, conforme linguagem).
- LOC (linhas de código), como métrica de controle para normalizar complexidade/duplicação.

## C) Variável independente

Uso ou não de assistente de IA generativa durante a resolução da tarefa (dois níveis: **com IA** / **sem IA**).

## D) Tratamentos

- **Tratamento A**: resolução do kata com assistente de IA habilitado (mesma ferramenta em todos os trials do grupo).
- **Tratamento B**: resolução do kata sem qualquer assistente de IA (codificação manual).

## E) Objetos experimentais

4 katas autorais de dificuldade comparável (ver `katas.json` e `validate_katas.py`), todos de nível "média", com tamanho estimado (LOC de referência) e número de testes de aceitação equivalentes entre si, escolhidos deliberadamente com baixa indexação para reduzir o risco de memorização pelo assistente de IA.

## F) Tipo de projeto experimental

**Crossover / within-subject, contrabalanceado**: cada integrante do trio resolve todos os 4 katas, metade com IA e metade sem IA, em ordem contrabalanceada entre os integrantes (para controlar efeito de ordem e de aprendizado). Esse desenho controla a variação individual de habilidade entre os participantes, já que cada pessoa serve como seu próprio controle.

## G) Quantidade de medições

3 integrantes × 4 katas = 12 trials no total (4 trials por integrante: 2 com IA + 2 sem IA), dentro da faixa de 4–6 trials/integrante recomendada pelo enunciado.

## H) Ameaças à validade

- **Efeito de aprendizado entre katas**: ao resolver múltiplos katas em sequência, o participante pode ficar mais rápido/eficiente nos últimos independentemente do tratamento. Mitigação: ordem contrabalanceada entre integrantes (nem todos resolvem os katas com IA primeiro).
- **Familiaridade prévia com a ferramenta de IA**: integrantes com mais experiência prévia no assistente escolhido podem ter vantagem não relacionada à ferramenta em si, mas à própria habilidade de "prompting". Mitigação: uso do mesmo assistente por todos, e menção explícita no relatório sobre o nível de experiência prévia de cada integrante.
- **Vazamento de solução já vista / memorização**: se os katas fossem exercícios muito conhecidos (ex.: clássicos do LeetCode/HackerRank), o assistente de IA poderia reproduzir uma solução memorizada de seu treinamento, em vez de efetivamente "ajudar" a resolver o problema do zero. Mitigação: uso de katas autorais do grupo, com variações deliberadas de nomenclatura e regras em relação a problemas clássicos conhecidos (ver campo `justificativa_baixa_indexacao` em cada kata).
- **Variação individual de habilidade entre integrantes**: mitigada pelo desenho within-subject (cada pessoa é comparada consigo mesma, não entre integrantes diferentes).
- **Pressão do time-box**: o limite de 35 minutos pode gerar comportamento diferente sob pressão de tempo entre tratamentos (ex.: desistir de refinar o código sem IA por falta de tempo, mas aceitar a primeira sugestão da IA sem revisão). Mitigação: reportar essa limitação na discussão final como possível viés a favor do tratamento mais rápido.
- **Trials do Artur em kata02 (ia) e kata04 (ia) resolvidos contra especificação desatualizada**: o código originalmente registrado nesses dois trials foi escrito contra uma versão antiga do enunciado dos katas (nomes de regra e formato de log diferentes dos que constam em `katas.json`), e por isso falhava quase totalmente (0/7 e 1/6) nos testes de aceitação oficiais, apesar de o registro informal do integrante indicar 7/7. Como não era possível refazer os trials dentro do time-box a tempo do fechamento da S02, o código desses dois trials foi **adaptado por um assistente de IA (Claude) após o fato**, só para bater com a especificação oficial — não pelo Artur, e não dentro do cronômetro do trial. Consequência: `tempo_segundos` desses dois trials (30 s e 42 s) reflete apenas o tempo do registro original do Artur contra a spec antiga, e **não inclui** o tempo da correção pós-hoc; `testes_passando`/`taxa_sucesso` (100%) refletem o código já corrigido, não o que o Artur de fato produziu sob o time-box. Mitigação/recomendação: tratar esses dois pontos com cautela na RQ1 (tempo pode estar subestimado) e, se possível, refazer os dois trials do zero em uma sessão futura para confirmar os números; até lá, reportar esta nota explicitamente na discussão de ameaças à validade do relatório final.

## Referência de métricas por RQ (justificativa da escolha)

- **RQ1**: métrica primária = tempo até passar todos os testes ("time-to-green"), agregado pela **mediana** por tratamento (não a média), dado o N pequeno e a sensibilidade da média a outliers/censura em 35 min.
- **RQ2**: métrica primária = taxa de sucesso (%), por normalizar katas com números diferentes de testes; nº absoluto de falhas como métrica complementar.
- **RQ3**: complexidade ciclomática média + % de duplicação, sempre reportados junto com LOC como controle (para não confundir "código mais verboso" com "código mais complexo").
- Todas as tabelas/gráficos descritivos usarão mediana e IQR (não média/desvio-padrão), e a análise inferencial usará teste de Wilcoxon (não paramétrico, adequado ao desenho within-subject com N pequeno).
