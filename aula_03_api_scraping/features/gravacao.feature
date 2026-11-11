# language: pt
Funcionalidade: Gravação de respostas brutas
  Como operador do monitor
  Quero preservar respostas de origem no MinIO
  Para que sejam auditáveis e reexecutáveis

  @RF-09
  @RNF-04
  @RNF-07
  Cenário: grava_html_bruto_bytes_e_metadados
    Dado que uma página HTML foi recebida como bytes
    Quando a resposta é gravada no raw
    Então os bytes permanecem inalterados
    E a chave é determinística e os metadados registram origem, instante e SHA-256

  @RF-10
  @RNF-07
  Cenário: grava_resposta_ptax_bruta_vazia
    Dado que a resposta PTAX é JSON válido com "value": []
    Quando a resposta é gravada no raw
    Então seus bytes e hash são preservados
    E a chave inclui fonte, moeda, data de referência, janela e hash

  @RF-09
  @RNF-07
  Cenário: reexecucao_reutiliza_chave_mesmo_conteudo
    Dado duas execuções na mesma data com os mesmos bytes e recurso
    Quando ambas gravam a resposta raw
    Então ambas referenciam a mesma chave determinística
    E o objeto existente não é alterado

  @RNF-04
  Cenário: metadados_ascii_estrito
    Dado metadados de origem para um objeto raw
    Quando os metadados são validados
    Então cada nome e valor pode ser codificado em ASCII estrito
    E qualquer valor não ASCII é rejeitado antes da gravação

  @RF-09
  @RNF-06
  @RNF-07
  Cenário: proxy_502_repete_put_mesma_chave
    Dado que o proxy Railway responde 502 antes de encaminhar o PUT
    Quando o gravador repete a gravação no bucket "teste"
    Então o retry envia os mesmos bytes para a mesma chave
    E o objeto confirmado tem o SHA-256 esperado

  @RF-09
  @RNF-04
  @RNF-10
  Cenário: minio_real_le_e_grava_no_bucket_teste
    Dado um MinIO local disponível e o bucket de teste "teste"
    Quando o objeto raw é gravado e lido do MinIO
    Então os bytes, o SHA-256 e os metadados ASCII correspondem ao objeto gravado
