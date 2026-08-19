## RQ03 + RQ04 — Extração de métricas via GraphQL

**Responsável:** João Santana

### Descrição
Implementar e validar a extração das métricas referentes a RQ03 (total de releases) e RQ04 (tempo até a última atualização), usando a GitHub GraphQL API, como parte da consulta única do grupo para os 100 repositórios mais populares.

### Critérios de aceite
- [ ] Query GraphQL retorna `releases { totalCount }` e `pushedAt`
- [ ] Script pagina corretamente até completar o número alvo de repositórios
- [ ] Validação manual feita em amostra de 5-10 repositórios (comparando com dados reais no GitHub)
- [ ] CSV de saída gerado com colunas: repo, stars, total_releases, pushed_at, days_since_update
- [ ] Critério de seleção dos repositórios (`stars:>1000 sort:stars-desc`) alinhado com os demais integrantes
- [ ] Código revisado e pronto para integração no script único do grupo

### Métricas
- RQ03: total de releases = `releases.totalCount`
- RQ04: tempo até a última atualização = data atual − `pushedAt`
