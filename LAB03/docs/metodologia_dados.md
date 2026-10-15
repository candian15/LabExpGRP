# Metodologia: fonte de dados, janela e seleção da amostra

> Parte do João na seção de Metodologia. Vem antes das definições operacionais (Artur) e da
> validação manual (Pedro). A versão LaTeX está em `metodologia_dados.tex`. Os números saem
> de `dados/funil.csv`, `dados/repositorios.csv` e do log da coleta.

## Fonte de dados e coleta

Todos os dados vêm da API REST do GitHub, consultada por um *pipeline* próprio em Python
que usa apenas a biblioteca `requests`, sem clientes prontos como o PyGithub. A coleta
inteira é reproduzida por um único comando (`python -m pipeline --config config.yaml`).
Cada resposta da API é gravada em um *cache* local e indexada pelo *hash* da URL. Assim,
uma coleta interrompida continua de onde parou, sem repetir chamadas. A execução final fez
11.989 chamadas à API e reaproveitou 58.459 respostas do *cache*.

Três limitações da API definiram o desenho da coleta:

- **Teto de 1.000 resultados por busca.** A busca de repositórios devolve no máximo 1.000
  itens por consulta, e só a faixa de 1.000 a 1.500 estrelas tem 20.493 repositórios. Por
  isso, a busca foi dividida em sete faixas de estrelas (1.000–1.500, 1.500–2.500,
  2.500–4.000, 4.000–7.000, 7.000–12.000, 12.000–25.000 e mais de 25.000). De cada faixa
  entraram os 1.000 repositórios mais estrelados, num total de 7.000 candidatos. Os
  candidatos foram avaliados alternando as faixas, e não em ordem decrescente de estrelas,
  para que a amostra não saísse inteira da faixa mais popular. A ordem é determinística.
- **Limite de requisições e instabilidade.** O cliente lê os cabeçalhos `X-RateLimit-*` e
  espera o *reset* quando a cota acaba. Erros 5xx e falhas de rede são repetidos com
  *backoff* exponencial (1 s, 2 s, 4 s, 8 s, 16 s), até seis tentativas.
- **Paginação e teto de *workflow runs*.** O cliente segue o cabeçalho `Link` em todas as
  listagens. A listagem de *runs* também devolve no máximo 1.000 resultados por consulta,
  e o `total_count` dela satura em 2.500. Por isso, os *runs* são pedidos mês a mês dentro
  da janela, e o mês que passa do teto é dividido ao meio até caber nele. O `total_count`
  serve apenas para decidir quando dividir, nunca como medida.

## Janela de observação

A janela tem 12 meses, de **01/10/2025 a 30/09/2026**, inclusiva nas duas pontas. Ela foi
definida pelo professor e é a mesma para todos os repositórios. Só entram releases
publicadas e *workflow runs* criados dentro dela, e só no *default branch*. A idade do
repositório é medida até o fim da janela, e não até a data da execução, para que uma
nova execução do *pipeline* chegue ao mesmo valor.

## Seleção da amostra

Os candidatos passaram por filtros em sequência. Cada repositório parou no primeiro filtro
em que falhou e por isso tem um único motivo de descarte. Os filtros mais caros em chamadas
à API vêm por último. A coleta parou ao completar 350 repositórios aprovados, acima do
mínimo de 300 exigido. A Tabela [[X]] mostra o funil.

| Etapa | Restantes | Descartados | Motivo do descarte |
|---|---:|---:|---|
| Candidatos da busca (7 faixas de estrelas) | 7.000 | — | — |
| Avaliados | 1.565 | 5.435 | não avaliados: a amostra já estava completa |
| Usam GitHub Actions | 1.057 | 508 | nenhum workflow em `/actions/workflows` |
| ≥ 5 releases publicadas na janela | 439 | 618 | menos de 5 releases na janela |
| *Runs* mensuráveis na janela | 433 | 6 | mais de 1.000 *runs* em um único dia |
| ≥ 50 *runs* válidos na janela | 352 | 81 | menos de 50 *runs* de `push` válidos no *default branch* |
| Coleta concluída sem erro | 350 | 2 | erro definitivo da API |
| **Amostra final** | **350** | — | — |

Três etapas merecem explicação:

- **Não avaliados.** Os 5.435 candidatos restantes nunca foram consultados, porque a
  coleta parou ao fechar a amostra. Eles não foram reprovados por nenhum critério e por
  isso aparecem numa etapa própria.
- **Repositórios hiperativos.** Seis repositórios tiveram mais de 1.000 *runs* em um único
  dia. Como não há filtro mais fino que a data e o `total_count` satura, não há como
  recuperar todos os *runs* desses dias, nem saber quantos faltam. Mantê-los faria o CFR (a)
  e o tempo de recuperação serem calculados sobre dados truncados de tamanho
  desconhecido. Preferimos descartá-los e registrar o descarte. Com isso, a amostra exclui
  os projetos de maior volume de CI.
- **Erros definitivos.** Dois repositórios foram perdidos depois de esgotadas as
  tentativas: um por HTTP 504 recorrente ao listar releases (`be5invis/Iosevka`) e outro
  porque a listagem de releases passou do limite de 10.000 resultados paginados da API,
  com HTTP 422 (`brave/brave-browser`).

A amostra final reúne 350 repositórios com 1.493 a 291.317 estrelas (mediana de 11.944).
Ela é concentrada nas faixas mais populares: 97 repositórios têm mais de 25.000 estrelas
e 27 estão na faixa de 1.000 a 1.500. As linguagens mais frequentes são TypeScript (73),
Python (72), Go (45), Rust (39) e JavaScript (28). Por repositório, a mediana é de 22
releases e 688 *runs* válidos na janela, e a idade mediana é de 6,0 anos.

A amostra **não é aleatória**. Dentro de cada faixa, só os 1.000 repositórios mais
estrelados chegaram a ser candidatos. Além disso, as faixas foram avaliadas na mesma
proporção, mas os repositórios mais populares passaram mais nos filtros, e por isso a
amostra final pende para eles. Os resultados valem para repositórios
populares que usam GitHub Actions e publicam releases, e não para o GitHub como um todo.
Essa limitação volta nas ameaças à validade.

## Dicionário de dados

O *pipeline* gera dois arquivos. O `repositorios.csv` tem uma linha por repositório
avaliado, aprovado ou descartado; os descartados têm o motivo preenchido e as métricas
vazias. O `funil.csv` tem uma linha por etapa da seleção. O dicionário completo, com tipo,
unidade e origem de cada coluna, está no repositório do trabalho (`DICIONARIO_DADOS.md`).
As colunas de `repositorios.csv` formam cinco grupos:

- **Metadados:** nome, estrelas, linguagem, *default branch*, data de criação, idade (até o
  fim da janela) e número de contribuidores.
- **Contagens da seleção:** releases publicadas na janela (sem rascunhos e pré-releases)
  e *runs* válidos. Um *run* é válido quando é de `push` no *default branch* e termina em
  sucesso ou falha. Os resultados `cancelled`, `skipped`, `neutral`, `action_required` e
  `stale` são ignorados.
- **Métricas DORA:** frequência de deploy (releases por semana), *lead time* nas variantes
  (a) e (b), CFR nas variantes (a) e (b) com as contagens da heurística de release
  corretiva, e tempo de recuperação com a proporção de episódios censurados.
- **Classificação:** nota de 1 a 4 por métrica, pelos cortes da disciplina, e categoria
  geral (Elite, High, Medium, Low), que é a mediana das notas disponíveis arredondada para
  baixo. A classificação usa a combinação de referência (release como deploy, *lead time* (a)
  e CFR (a)). As variantes (b) ficam no arquivo para a análise de sensibilidade.
- **Seleção:** o motivo do descarte, vazio para os aprovados.

Três convenções valem para todos os campos. Vazio significa **não medido** e é diferente
de zero. Datas estão em UTC. Decimais têm quatro casas. Métrica vazia não recebe nota e fica
fora da mediana da categoria geral.
