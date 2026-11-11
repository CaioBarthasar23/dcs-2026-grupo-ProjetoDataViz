# Regras de negócio · Monitor de preços

## RN-01 · Identidade do livro

- **Enunciado:** cada livro é identificado pelo UPC informado em sua página de detalhe.
- **Origem:** DN-03, OBJ-03, P3.
- **Exemplo:** duas observações com o mesmo UPC ilustrativo `1111111111111` referem-se ao mesmo livro, ainda que o título tenha sido corrigido.
- **Contraexemplo:** tratar duas observações do mesmo UPC como livros diferentes apenas porque o título mudou.

## RN-02 · Cotação válida para a data de referência

- **Enunciado:** para a data D, vale a cotação GBP/BRL do último boletim “Fechamento” cuja data seja menor ou igual a D, e a data efetiva da cotação deve permanecer visível.
- **Origem:** DN-01, OBJ-01, P1.
- **Exemplo:** para sábado, 24/10/2026, usar o fechamento de sexta-feira, 23/10/2026, exibindo 23/10/2026 como data da cotação.
- **Contraexemplo:** para 24/10/2026, usar o boletim “Abertura” de sexta-feira, 23/10, em vez do último “Fechamento” disponível, também de 23/10.

## RN-03 · Data local da coleta

- **Enunciado:** a data de referência de cada coleta é o dia do calendário local de São Paulo em que ela ocorre.
- **Origem:** restrição do pedido: data de referência pelo calendário local de São Paulo.
- **Exemplo:** uma coleta às 23h30 de 10/11 em São Paulo pertence a 10/11, mesmo que em outro fuso já seja 11/11.
- **Contraexemplo:** registrar a coleta como 11/11 porque em outro fuso já virou o dia.

## RN-04 · Respeito às instruções de acesso

- **Enunciado:** a coleta respeita as permissões e proibições de acesso publicadas pelo site.
- **Origem:** restrição da disciplina: respeitar as instruções de acesso do site.
- **Exemplo:** consultar as instruções antes de coletar e deixar de acessar um caminho que elas proíbem.
- **Contraexemplo:** coletar um caminho proibido porque ele contém dados úteis.

## RN-05 · Identificação da coleta

- **Enunciado:** toda coleta informa claramente que é realizada pelo monitor do grupo.
- **Origem:** restrição da disciplina: identificação clara do responsável pela coleta.
- **Exemplo:** informar que a coleta é feita pelo monitor de preços do grupo.
- **Contraexemplo:** realizar a coleta sem informar quem é responsável por ela.

## RN-06 · Consultas sequenciais

- **Enunciado:** as páginas são consultadas uma por vez, sem consultas paralelas.
- **Origem:** restrição da disciplina: coleta sem paralelismo.
- **Exemplo:** terminar a consulta de uma página antes de iniciar a próxima.
- **Contraexemplo:** solicitar simultaneamente todas as páginas de uma categoria.

## RN-07 · Intervalo entre consultas

- **Enunciado:** a coleta aguarda o intervalo definido entre consultas consecutivas.
- **Origem:** restrição da disciplina: intervalo entre requisições.
- **Exemplo:** aguardar o intervalo aprovado antes de consultar a página seguinte.
- **Contraexemplo:** iniciar a consulta seguinte imediatamente, sem respeitar o intervalo.

## RN-08 · Preservação do dado bruto

- **Enunciado:** o conteúdo original é guardado antes de qualquer interpretação e não é alterado depois de guardado.
- **Origem:** restrição do pedido: preservar o conteúdo bruto antes de interpretar e não alterá-lo.
- **Exemplo:** preservar exatamente a resposta recebida e usar uma cópia para extrair preço e UPC.
- **Contraexemplo:** normalizar ou editar o conteúdo original antes de preservá-lo.

## RN-09 · Reexecução no mesmo dia

- **Enunciado:** uma nova execução para a mesma data de referência substitui o resultado anterior, sem criar uma segunda cópia do mesmo resultado diário.
- **Origem:** restrição do pedido: reexecução diária substitui sem duplicar; P2.
- **Exemplo:** reexecutar a coleta de 10/11 atualiza o resultado atribuído a 10/11.
- **Contraexemplo:** manter duas execuções indistinguíveis como resultados do dia 10/11.

## RN-10 · Incompletude visível no escopo coletado

- **Enunciado:** se a quantidade de livros extraídos diferir do total declarado para o escopo coletado, a execução é marcada como falha e a divergência fica registrada; o total da página inicial vale para coleta completa e, com filtro, valem os totais declarados das categorias selecionadas.
- **Origem:** restrição do pedido: divergência marca falha registrada; P2.
- **Exemplo:** em 03/10/2026, a página declara 1.000 resultados e são extraídos 999; registrar a divergência e marcar falha.
- **Contraexemplo:** uma categoria selecionada declara 32 resultados e são extraídos 31; marcar sucesso sem registrar a divergência.

## RN-11 · Atributos correspondentes à observação do livro

- **Enunciado:** os atributos registrados para um livro correspondem à mesma observação coletada, mantendo os valores apresentados pela listagem e pelo detalhe sem conversão de moeda.
- **Origem:** DN-01, DN-03, OBJ-01, OBJ-03, P1, P3.
- **Exemplo:** para o UPC `e00eb4fd7b871a48`, registrar o preço observado em libras, o rótulo original da avaliação e a disponibilidade consultada no detalhe.
- **Contraexemplo:** associar ao UPC de um livro o preço ou a avaliação de outro título da página.

## Rastreabilidade

| RN | Origem |
|---|---|
| RN-01 | DN-03, OBJ-03, P3 |
| RN-02 | DN-01, OBJ-01, P1 |
| RN-03 | Restrição do pedido: data de referência pelo calendário local de São Paulo |
| RN-04 | Restrição da disciplina: respeitar as instruções de acesso do site |
| RN-05 | Restrição da disciplina: identificar o responsável pela coleta |
| RN-06 | Restrição da disciplina: sem paralelismo |
| RN-07 | Restrição da disciplina: intervalo entre consultas |
| RN-08 | Restrição do pedido: preservar o conteúdo bruto |
| RN-09 | Restrição do pedido: reexecução sem duplicar; P2 |
| RN-10 | Restrição do pedido: divergência registrada como falha no escopo coletado; P2 |
| RN-11 | DN-01, DN-03, OBJ-01, OBJ-03, P1, P3 |
