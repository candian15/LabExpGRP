## RQ01 + RQ02 — Extração de métricas via GraphQL

**Responsável:** (seu nome)

### Descrição
Implementar e validar a extração das métricas referentes a RQ01 (idade do repositório) e RQ02 (total de pull requests aceitas), usando a GitHub GraphQL API, como parte da consulta única do grupo para os 100 repositórios mais populares.

### Critérios de aceite
- [ ] Query GraphQL retorna `createdAt` e `pullRequests(states: MERGED) { totalCount }`
- [ ] Script pagina corretamente até completar o número alvo de repositórios
- [ ] Validação manual feita em amostra de 5-10 repositórios (comparando com dados reais no GitHub)
- [ ] CSV de saída gerado com colunas: repo, stars, created_at, age_years, merged_prs
- [ ] Critério de seleção dos repositórios (`stars:>1000 sort:stars-desc`) alinhado com os demais integrantes
- [ ] Código revisado e pronto para integração no script único do grupo

### Métricas
- RQ01: idade do repositório = data atual − `createdAt`
- RQ02: total de PRs aceitas = `pullRequests(states: MERGED).totalCount`
