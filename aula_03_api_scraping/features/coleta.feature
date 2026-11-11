# language: pt
Funcionalidade: Coleta de Books to Scrape e PTAX
  Como operador do monitor
  Quero coletar fontes de forma educada e rastreável
  Para obter respostas brutas e cotações elegíveis

  @RF-01
  Cenário: descobre_categorias_sem_total_fixo
    Dado a página inicial em "tests/fixtures/inicio.html"
    Quando o coletor descobre as categorias
    Então cada categoria publicada na página é retornada com seu endereço
    E a descoberta não depende de uma quantidade fixa de categorias

  @RF-02
  Cenário: pagina_next_ate_fim
    Dado a categoria Mystery em "tests/fixtures/categoria_mystery_p1.html" e a página seguinte em "tests/fixtures/categoria_mystery_p2.html"
    Quando o coletor percorre o link next até não haver próximo endereço
    Então as duas páginas da categoria são consultadas uma vez cada
    E a paginação termina sem duplicar livros

  @RF-03
  Cenário: filtro_categorias_configurado
    Dado que SCRAPER_CATEGORIAS contém "mystery"
    Quando o escopo da coleta é definido
    Então somente a categoria configurada é coletada
    Dado que SCRAPER_CATEGORIAS está vazia
    Quando o escopo da coleta é definido novamente
    Então todas as categorias descobertas são coletadas

  @RF-04
  Cenário: visita_detalhe_para_upc_estoque_categoria
    Dado a listagem Mystery e o detalhe em "tests/fixtures/detalhe_sharp_objects.html"
    Quando o coletor processa Sharp Objects
    Então UPC, disponibilidade e categoria vêm do detalhe
    E título e preço correspondem à mesma observação da listagem

  @RF-05
  Cenário: registra_robots_404_sem_inferir_permissao
    Dado que robots.txt retorna HTTP 404
    Quando o coletor registra a resposta
    Então endereço, horário, status e corpo são registrados
    E nenhuma regra de permissão é inventada

  @RF-06
  Cenário: user_agent_intervalo_e_sequencial
    Dado que o cliente tem User-Agent identificável e intervalo configurado
    Quando duas páginas do site são solicitadas
    Então no máximo uma requisição fica ativa por vez
    E o início da próxima respeita o intervalo mínimo desde o início da anterior

  @RF-07
  Cenário: consulta_ptax_e_seleciona_fechamento
    Dado uma janela PTAX válida para GBP até a data de referência
    Quando a resposta contém mais de um boletim Fechamento elegível
    Então o fechamento mais recente até a data de referência é selecionado
    E a data efetiva da cotação permanece visível

  @RF-08
  Cenário: ptax_sem_fechamento_marca_incompleta
    Dado que a PTAX responde HTTP 200 com "value": []
    Quando a janela é processada
    Então a resposta vazia é registrada
    E a execução fica incompleta sem criar cotação

  @RF-08
  Cenário: ptax_sem_fechamento_elegivel_marca_incompleta
    Dado que a PTAX responde HTTP 200 com boletins mas nenhum Fechamento até a data de referência
    Quando a janela é processada
    Então a resposta é preservada
    E a execução fica incompleta sem criar cotação

  @RF-16
  Cenário: envia_data_ptax_no_formato_aceito
    Dado datas válidas para início e fim da janela PTAX
    Quando a URL de consulta é preparada
    Então ambas as datas usam MM-DD-AAAA

  @RF-16
  Cenário: ptax_http_500_registra_falha_de_consulta
    Dado que a API PTAX responde HTTP 500 à consulta
    Quando a resposta da consulta é processada
    Então a falha HTTP é registrada no resultado da execução
    E não é classificada como janela vazia

  @RNF-02
  Cenário: timeout_explicito_conexao_leitura
    Dado uma requisição HTTP simulada que não responde
    Quando o cliente envia a requisição
    Então timeout finito explícito é aplicado à conexão e à leitura
    E o cliente termina a tentativa por timeout dentro do limite total de 15 segundos

  @RNF-06
  Cenário: respeita_retry_after_em_429
    Dado que a fonte responde 429 com Retry-After de 2 segundos e depois 200
    Quando o cliente repete a consulta
    Então a espera simulada é exatamente 2 segundos
    E os bytes da resposta 200 são devolvidos

  @RNF-06
  Cenário: repete_read_timeout_e_5xx_com_limite
    Dado que tentativas terminam em erro de conexão, read timeout, HTTP 408 ou HTTP 503
    Quando o cliente aplica a política de retry
    Então somente falhas transitórias são repetidas com full jitter
    E a quantidade total não supera o limite configurado

  @RNF-06
  Cenário: nao_repete_outros_4xx
    Dado que a fonte responde com um HTTP 4xx permanente diferente de 408 e 429
    Quando o cliente processa a resposta
    Então a requisição não é repetida
    E a falha é devolvida ao coletor
