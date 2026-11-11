# language: pt
Funcionalidade: Controle e rastreabilidade das execuções
  Como operador do pipeline
  Quero registrar estado e histórico de cada execução
  Para diagnosticar falhas e reexecutar sem duplicar

  @RF-13
  @RNF-05
  Cenário: manifesto_registra_execucao_e_itens
    Dado que uma execução começou e consultou recursos
    Quando a execução termina
    Então um manifesto próprio registra id, datas, estado, totais e fontes
    E cada item inclui status, tentativas, bytes, hash e erro quando houver

  @RF-13
  @RNF-05
  Cenário: item_falhou_permanece_no_manifesto_com_causa
    Dado que um item esgotou as tentativas ou teve erro permanente
    Quando o manifesto é finalizado
    Então o item fica no estado falhou com a causa registrada
    E não aponta para um objeto raw não confirmado

  @RF-14
  @RNF-01
  Cenário: divergencia_contagem_completa_ou_filtrada_marca_falha
    Dado uma coleta completa ou de categorias filtradas
    Quando o total extraído é comparado ao total declarado correspondente
    Então qualquer diferença marca falha e registra a diferença numérica

  @RF-15
  @RNF-07
  Cenário: reexecucao_substitui_bronze_sem_duplicar
    Dado que já existem resultados para a data D
    Quando outra execução para D termina com validação aprovada
    Então os JSON Lines diários passam a representar o resultado mais recente sem duplicatas
    E o manifesto anterior e os objetos raw permanecem preservados

  @RNF-08
  Cenário: configuracao_nao_expoe_segredos
    Dado que credenciais estão em variáveis de ambiente de configuração
    Quando a configuração é carregada e erros são reportados
    Então nenhum valor secreto aparece em logs, mensagens ou arquivos versionados

  @RNF-10
  Cenário: mesmo_codigo_usa_minio_local_ou_railway
    Dado a mesma versão do código e configurações válidas para cada MinIO
    Quando a suíte de armazenamento é executada em cada destino
    Então a mesma interface e resultados funcionais são preservados
    E somente o arquivo de ambiente muda

  @RNF-03
  Cenário: duracao_coleta_completa_e_registrada
    Dado uma execução completa com relógio monotônico controlado
    Quando o pipeline mede o tempo entre início e término
    Então a duração é calculada em segundos
    E uma duração superior a 30 minutos é registrada como falha da execução
