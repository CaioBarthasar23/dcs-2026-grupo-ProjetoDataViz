# language: pt
Funcionalidade: Extração dos objetos brutos
  Como engenheiro de dados da Aula 04
  Quero transformar os objetos raw em JSON Lines
  Para consumir registros consistentes sem consultar fontes externas

  @RF-11
  @RNF-09
  Cenário: le_so_minio_sem_chamada_http
    Dado que o manifesto referencia HTML raw no MinIO
    Quando o extrator processa os objetos
    Então ele lê somente do MinIO
    E nenhuma função HTTP nem fonte externa é chamada

  @RF-11
  @RNF-01
  Cenário: extrai_upc_estoque_e_preco_das_fixtures
    Dado a listagem e o detalhe Sharp Objects nas fixtures
    Quando o extrator processa os bytes
    Então o upc é "e00eb4fd7b871a48"
    E o preco_gbp é 47.82
    E a qtd_estoque é 20

  @RF-11
  @RNF-01
  Cenário: decodifica_charset_sem_alterar_raw
    Dado que o HTML informa charset no documento mas não no Content-Type
    Quando o parser decodifica a cópia para extrair texto
    Então os campos textuais são preservados corretamente
    E os bytes armazenados no raw permanecem inalterados

  @RF-11
  @RNF-01
  Cenário: avaliacao_preserva_rotulo
    Dado que a listagem apresenta uma classe star-rating
    Quando o livro é serializado
    Então avaliacao contém o rótulo original One, Two, Three, Four ou Five
    E não é convertida em número

  @RF-11
  @RNF-01
  Cenário: livro_serializa_exatamente_nove_campos
    Dado um registro Livro válido
    Quando a linha JSON Lines é serializada
    Então ela contém exatamente upc, url, titulo, categoria, avaliacao, preco_gbp, em_estoque, qtd_estoque e coletado_em

  @RF-12
  @RNF-01
  Cenário: cotacao_emite_campos_exatos
    Dado que o JSON bruto contém um Fechamento GBP elegível
    Quando a cotação é extraída
    Então a linha contém exatamente moeda, dataHoraCotacao, tipoBoletim, cotacaoCompra e cotacaoVenda
    E a data efetiva permanece em dataHoraCotacao

  @RF-14
  @RNF-01
  Cenário: divergencia_contagem_bloqueia_publicacao
    Dado que o total extraído difere do total declarado no escopo
    Quando o resultado é validado
    Então a execução é marcada como falha com a diferença registrada
    E o resultado incompleto não é publicado como sucesso
