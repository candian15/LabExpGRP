# Protocolo da validação manual

Aqui explicamos como fizemos a validação manual da amostra-ouro (seção 6 do enunciado). A ideia é conferir se a nossa heurística de release corretiva acerta, comparando a saída dela com o que nós três decidimos olhando os repositórios.

## Sorteio

Sorteamos 60 repositórios da amostra final com `random_state=42`, para que qualquer pessoa consiga repetir o sorteio e chegar nos mesmos repositórios. Antes de sortear, ordenamos os repositórios pelo nome, assim o resultado não muda se a coleta gravar o CSV em outra ordem.

De cada repositório sorteamos 5 releases, com a mesma semente. Só entram releases que têm uma release anterior, porque sem a lista de commits entre as duas não conseguimos dizer se ela foi corretiva. Se um repositório tiver menos de 5 releases assim, ele entra com as que tiver.

## Rotulagem

Cada um de nós preenche a sua própria planilha (`rotulos_artur.csv`, `rotulos_joao.csv` e `rotulos_pedro.csv`). Combinamos três regras:

- não conversar sobre os rótulos antes de todos terminarem;
- não abrir a planilha dos outros;
- não olhar a saída da heurística antes de terminar a própria planilha.

Na planilha, as linhas `repositorio` pedem duas respostas:

- **tipo_projeto**: `biblioteca` (usada como dependência por outros projetos), `aplicacao` (aplicação ou serviço usado diretamente), `cli` (ferramenta de linha de comando) ou `outro`. Na dúvida, seguimos o que o README diz que o projeto é.
- **entregas_reais**: `sim` se as releases publicam uma versão que o usuário instala ou usa, `nao` se são só marcos ou automação, e `incerto` se não der para saber.

As linhas `release` pedem só uma:

- **corretiva**: `sim` se o objetivo principal da release foi corrigir um bug recente, `nao` caso contrário. Para decidir, lemos as release notes (coluna `link`) e os commits (coluna `link_commits`). Se a release mistura correções e novidades, vale o que for o foco principal.

A coluna `observacao` é livre e serve para anotar dúvidas que queremos discutir depois. No Excel, a planilha precisa ser salva como **CSV UTF-8**.

## Concordância

Depois que os três terminam, calculamos o kappa de Fleiss em cada uma das três perguntas. Ele mostra o quanto concordamos descontando o que concordaríamos por sorte. Para interpretar o valor, usamos a escala de Landis & Koch (1977). Se o kappa ficar baixo, isso quer dizer que até para nós o critério é ambíguo, e isso entra na discussão do artigo.

## Consenso e desempate

- Se pelo menos 2 de nós deram a mesma resposta, ela vira o rótulo final.
- Se não houver maioria (por exemplo, cada um escolheu um tipo de projeto diferente), o caso vai para o arquivo `desempate.csv`.
- Fazemos uma reunião com os três, olhamos o repositório ou a release juntos e escrevemos a decisão na coluna `decisao`.
- Depois rodamos o script de consenso de novo.

O resultado final fica em `consenso.csv`, que o Artur usa para avaliar a heurística, e em `consenso_repos.csv`, que usamos na RQ 06.

## Registro

| Etapa | Data | Observação |
|---|---|---|
| Sorteio | | |
| Rotulagem | | |
| Reunião de desempate | | |