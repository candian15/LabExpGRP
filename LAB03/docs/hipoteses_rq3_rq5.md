# Hipóteses informais (Introdução do artigo)

> As das RQ 03 a 05 foram escritas antes da coleta; as das RQ 01, 02, 06, 07 e 08, depois,
> a partir da literatura. A versão condensada, usada no artigo, está em `hipoteses_rq3_rq5.tex`.

As hipóteses das RQ 03 a 05 foram registradas antes da coleta. As das RQ 01, 02, 06, 07 e 08
foram formuladas depois, a partir da literatura e do que se costuma esperar de projetos
open-source, sem ajustá-las aos resultados. A tabela "Hipóteses e resultados", na Discussão,
confronta cada uma com o que foi observado.

**RQ 01 (formulada depois da coleta).** A maioria dos projetos deve publicar menos de uma
release por semana, com mediana entre uma por mês e uma por semana (faixa *Medium*), já que
releases open-source costumam agrupar várias mudanças.

**RQ 02 (formulada depois da coleta).** O *lead time* deve ser de semanas (mediana entre uma
semana e 30 dias), com a variante (a) maior que a (b), porque ela mede a partir do *commit*
mais antigo de cada release.

**RQ 03: taxa de falha das mudanças.** Esperamos que a variante de CI (a)
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

**RQ 04: tempo de recuperação.** Esperamos uma mediana da ordem de algumas
horas, o que colocaria a maioria dos repositórios na faixa *High* (1 hora a
menos de 1 dia). Em projetos ativos, a falha costuma ser resolvida pelo
próximo *push*, seja uma correção, um *revert* ou uma nova execução bem-sucedida.
Esperamos, porém, uma cauda longa e um IQR largo, de minutos a vários dias,
porque mantenedores de projetos open-source trabalham de forma voluntária e
assíncrona e alguns workflows rodam raramente. Pelo mesmo motivo, esperamos uma
proporção não trivial de episódios censurados, concentrada nos workflows menos
executados.

**RQ 05: frequência de deploy × taxa de falha.** Para a variante (a),
esperamos uma correlação de Spearman fraca e negativa ou nula, em linha com a
afirmação do DORA de que velocidade e estabilidade não são um *trade-off*.
Projetos que publicam com frequência tendem a ter automação e cobertura de
testes mais maduras. Para a variante (b), esperamos o oposto: uma correlação
positiva. Essa correlação viria em parte de um artefato da própria métrica, e
não necessariamente de pior qualidade. Quem publica muitas releases tem mais
chances de publicar um *patch* em até 7 dias após qualquer release, e então a
release anterior é marcada como falha. Se isso se confirmar, a resposta da RQ 05 depende
da definição operacional, assim como a análise de sensibilidade da RQ 07 investiga.

**RQ 06 (formulada depois da coleta).** Projetos mais populares e com mais contribuidores
devem ter desempenho melhor (publicar mais e com *lead time* menor), projetos mais antigos
devem publicar menos, com ritmo mais estável, e a linguagem deve ter pouco efeito.

**RQ 07 (formulada depois da coleta).** A classificação deve ser razoavelmente robusta, com
menos de 20% dos repositórios mudando de categoria, porque pré-releases e tags costumam
acompanhar as releases; usar tags deve aumentar a frequência e o número de repositórios
*Elite*.

**RQ 08 (formulada depois da coleta).** O *rework rate* deve ser maior que o CFR (b), por
contar toda release corretiva, e ficar em torno de um terço das releases.
