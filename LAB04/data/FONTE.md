# Fonte dos dados reais

**Cenário:** tempo até o merge de PRs com e sem bot de revisão (par P1: t de Welch × Mann-Whitney).

| Item | Valor |
|---|---|
| Repositório | [`ant-design/ant-design`](https://github.com/ant-design/ant-design) (público) |
| Bot de revisão | `copilot-pull-request-reviewer` (revisão automática do GitHub Copilot) |
| Janela | PRs criados entre 2026-07-01 e 2026-10-31 e já mesclados |
| Data da coleta | 2026-11-04 |
| Método | API de busca do GitHub (`GET /search/issues`), sem token, com `src/coletar_dados_reais.py` |
| Variável | `horas_ate_merge` = `merged_at` − `created_at`, em horas |

## Como os grupos foram definidos

- **com_bot:** PRs mesclados em que o bot comentou/revisou (`commenter:app/copilot-pull-request-reviewer`). Elegíveis: 190.
- **sem_bot:** PRs mesclados na mesma janela em que o bot **não** comentou (`-commenter:app/copilot-pull-request-reviewer`). Elegíveis: 455.
- PRs abertos por contas de bot (ex.: dependabot) foram excluídos.
- De cada grupo foram sorteados **30 PRs** com `numpy.random.default_rng(42)`. O conjunto completo de elegíveis está em `pool_completo.csv`.

## Arquivos

- `dados_reais.csv`: a amostra de 60 PRs (30 por grupo) usada no laboratório.
- `pool_completo.csv`: todos os PRs elegíveis (para conferência da amostragem).
- `estatisticas_descritivas.csv`: mediana, IQR, assimetria, outliers e normalidade de cada grupo.

## Limitações (entram na seção de Conclusão)

- **Não é um experimento:** o bot não foi atribuído aleatoriamente aos PRs. Quem decide acionar a revisão do Copilot pode escolher PRs de tipos diferentes (menores, de mantenedores, etc.), então a diferença observada não prova que o bot causa o menor tempo de merge.
- O papel dos dados reais aqui é só deixar a simulação realista e servir de aplicação final.
- Uma única janela de 4 meses e um único repositório.
- A reprodução exata depende de a API devolver o mesmo conjunto de PRs; por isso o `dados_reais.csv` é commitado.
