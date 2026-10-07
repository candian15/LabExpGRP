# Hipóteses informais — RQ 03, RQ 04 e RQ 05 (Introdução do artigo)

> Escritas antes da coleta, como pede o enunciado. Texto pronto para o João
> juntar na Introdução; a versão LaTeX está em `hipoteses_rq3_rq5.tex`.

**RQ 03 — Taxa de falha das mudanças.** Esperamos que a variante de CI (a)
fique, na mediana, entre 10% e 25%. Como os runs considerados são disparados
por *push* no default branch, boa parte das mudanças já passou pela validação de
um *pull request* antes do *merge*. Ainda assim, problemas de integração,
testes instáveis (*flaky*) e dependências externas devem gerar uma fração não
desprezível de falhas. Para a variante de entrega (b), esperamos valores
parecidos ou menores e uma distribuição com muitos repositórios em 0%. Releases
seguidas de uma correção em até 7 dias devem ser relativamente raras em
projetos que publicam com pouca frequência. Também esperamos que as duas
variantes concordem pouco entre si, porque a variante (a) mede falha de
*pipeline* e a (b) aproxima falha percebida pelo usuário.

**RQ 04 — Tempo de recuperação.** Esperamos uma mediana da ordem de algumas
horas, o que colocaria a maioria dos repositórios na faixa *High* (1 hora a
menos de 1 dia). Em projetos ativos, a falha costuma ser resolvida pelo
próximo *push*, seja uma correção, um *revert* ou uma nova execução bem-sucedida.
Esperamos, porém, uma cauda longa e um IQR largo, de minutos a vários dias,
porque mantenedores de projetos open-source trabalham de forma voluntária e
assíncrona e alguns workflows rodam raramente. Pelo mesmo motivo, esperamos uma
proporção não trivial de episódios censurados, concentrada nos workflows menos
executados.

**RQ 05 — Frequência de deploy × taxa de falha.** Para a variante (a),
esperamos uma correlação de Spearman fraca e negativa ou nula, em linha com a
afirmação do DORA de que velocidade e estabilidade não são um *trade-off*.
Projetos que publicam com frequência tendem a ter automação e cobertura de
testes mais maduras. Para a variante (b), esperamos o oposto: uma correlação
positiva. Essa correlação viria em parte de um artefato da própria métrica, e
não necessariamente de pior qualidade. Quem publica muitas releases tem mais
chances de publicar um *patch* em até 7 dias após qualquer release, e então a
release anterior é marcada como falha. Se isso se confirmar, será evidência de
que a conclusão da RQ 05 depende da definição operacional escolhida, o que
conecta esta questão à análise de sensibilidade da RQ 07.
