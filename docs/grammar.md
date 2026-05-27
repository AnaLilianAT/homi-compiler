# Gramatica da Linguagem Homi

Este documento define a Gramatica Livre de Contexto (GLC) da linguagem Homi em sua versao projetada para cobrir os padroes observados em `examples/professor/automations_homi.yaml`.

O parser ainda nao foi atualizado para reconhecer toda essa linguagem. Nesta etapa, a meta e documentar a sintaxe alvo e representa-la em `src/grammar.py` de forma organizada e pronta para a futura construcao da tabela LL(1).

## Ajustes LL(1)

Na implementacao sintatica, a gramatica passou por pequenos ajustes estruturais para manter a propriedade LL(1):

- `sun_trigger_core` foi fatorada para evitar prefixo comum entre `sol evento ...` e `sol evento offset ...`
- literais booleanos foram isolados em um nao-terminal proprio
- duracoes ficaram separadas de strings comuns na gramatica executavel do parser
- comparacoes como `bateria abaixo 20` passaram a aceitar metricas reservadas explicitamente

## Objetivos de projeto

- Cobrir automacoes com `alias`, `description`, `triggers`, `conditions`, `actions` e `mode`.
- Cobrir gatilhos `state`, `device`, `time` e `sun`.
- Cobrir condicoes `state`, `device`, `trigger`, `time`, `sun`, `or` e `and`.
- Cobrir acoes por dispositivo, acoes por servico, `delay`, `if/then/else` e `choose/case`.
- Cobrir `target`, `data`, `metadata`, listas e `enabled`.
- Manter uma sintaxe amigavel, mas com secoes explicitas e producoes pensadas para LL(1).

## Terminais

### Palavras reservadas

- `entidade`
- `dispositivo`
- `automacao`
- `modo`
- `single`
- `restart`
- `descricao`
- `gatilhos`
- `quando`
- `estado`
- `device_id`
- `entity_id`
- `condicoes`
- `se`
- `igual`
- `de`
- `para`
- `por`
- `hora`
- `dias`
- `horario`
- `entre`
- `e`
- `antes`
- `depois`
- `sol`
- `nascer_do_sol`
- `por_do_sol`
- `offset`
- `gatilho`
- `em`
- `qualquer`
- `todos`
- `acoes`
- `faca`
- `ligar`
- `desligar`
- `alternar`
- `abrir`
- `fechar`
- `servico`
- `alvo`
- `dados`
- `metadados`
- `espere`
- `entao`
- `senao`
- `escolha`
- `caso`
- `id`
- `apelido`
- `habilitado`
- `acima`
- `abaixo`
- `ligado`
- `desligado`
- `armado`
- `desarmado`
- `movimento`
- `aberto`
- `fechado`
- `nao_aberto`
- `seg`
- `ter`
- `qua`
- `qui`
- `sex`
- `sab`
- `dom`

### Pontuacao

- `=`
- `{`
- `}`
- `[`
- `]`
- `:`
- `;`
- `,`

### Classes lexicas

- `IDENT`
- `QUALIFIED_NAME`
- `STRING`
- `NUMBER`
- `BOOL`
- `DURATION`
- `EOF`

Observacoes:

- `QUALIFIED_NAME` representa nomes pontuados por dominio, como `light.sala`, `switch.turn_on`, `notify.mobile_app_zfold4`.
- `DURATION` representa literais como `45s`, `5min`, `1min45s`.
- `BOOL` representa `true` ou `false`.

## Nao-terminais

```text
<programa>
<lista_topo>
<item_topo>
<decl_entidade>
<decl_dispositivo>
<decl_automacao>
<modo>
<bloco_automacao>
<secao_descricao_opt>
<secao_descricao>
<secao_gatilhos_opt>
<secao_gatilhos>
<lista_gatilhos_opt>
<gatilho>
<gatilho_corpo>
<gatilho_estado>
<gatilho_dispositivo>
<gatilho_sol>
<gatilho_hora>
<de_estado_opt>
<modo_dispositivo>
<alias_gatilho_opt>
<id_gatilho_opt>
<duracao_gatilho_opt>
<dias_opt>
<lista_dias>
<lista_dias_tail_opt>
<dia_semana>
<evento_sol>
<comparador>
<secao_condicoes_opt>
<secao_condicoes>
<lista_condicoes_opt>
<comando_condicao>
<lista_entradas_condicao_opt>
<entrada_condicao>
<clausula_condicao>
<condicao_simples>
<condicao_logica>
<condicao_estado>
<condicao_dispositivo>
<modo_condicao_dispositivo>
<condicao_gatilho>
<condicao_horario>
<modo_condicao_horario>
<antes_horario_opt>
<depois_horario_opt>
<condicao_sol>
<modo_condicao_sol>
<depois_sol_opt>
<antes_sol_opt>
<habilitado_condicao_opt>
<secao_acoes_opt>
<secao_acoes>
<lista_acoes_opt>
<acao>
<acao_simples>
<acao_em_bloco>
<comando_acao>
<acao_dispositivo>
<verbo_dispositivo>
<acao_servico>
<alvo_opt>
<dados_opt>
<metadados_opt>
<habilitado_acao_opt>
<acao_se>
<senao_opt>
<bloco_acoes>
<acao_escolha>
<lista_casos_opt>
<caso_escolha>
<bloco_alvo>
<lista_alvos_opt>
<entrada_alvo>
<valor_entity_id>
<valor_device_id>
<mapa>
<lista_campos_opt>
<campo>
<chave_mapa>
<valor>
<valor_atomico>
<valor_basico>
<valor_basico_ou_lista>
<lista_valores_basicos>
<lista_valores_basicos_tail_opt>
<lista_valores>
<lista_valores_tail_opt>
<seletor_ids_gatilho>
<lista_ids_gatilho>
<lista_ids_gatilho_tail_opt>
<id_gatilho_valor>
<seletor_entidades>
<lista_entidades>
<lista_entidades_tail_opt>
<ref_entidade>
<sujeito_dispositivo>
<sujeito_dispositivo_tail>
<valor_duracao>
<linhas_em_branco_opt>
```

## GLC completa

```text
<programa> ::= <linhas_em_branco_opt> <lista_topo> EOF

<lista_topo> ::= <item_topo> <linhas_em_branco_opt> <lista_topo>
               | EPSILON

<item_topo> ::= <decl_entidade>
              | <decl_dispositivo>
              | <decl_automacao>

<decl_entidade> ::= "entidade" IDENT "=" QUALIFIED_NAME ";"

<decl_dispositivo> ::= "dispositivo" IDENT "=" IDENT "device_id" STRING "entity_id" STRING ";"

<decl_automacao> ::= "automacao" STRING "modo" <modo> <bloco_automacao>

<modo> ::= "single"
         | "restart"

<bloco_automacao> ::= "{"
                      <secao_descricao_opt>
                      <secao_gatilhos_opt>
                      <secao_condicoes_opt>
                      <secao_acoes_opt>
                      "}"

<secao_descricao_opt> ::= <secao_descricao>
                        | EPSILON

<secao_descricao> ::= "descricao" STRING ";"

<secao_gatilhos_opt> ::= <secao_gatilhos>
                       | EPSILON

<secao_gatilhos> ::= "gatilhos" "{" <lista_gatilhos_opt> "}"

<lista_gatilhos_opt> ::= <gatilho> <lista_gatilhos_opt>
                       | EPSILON

<gatilho> ::= "quando" <gatilho_corpo> ";"

<gatilho_corpo> ::= "estado" <gatilho_estado>
                  | "dispositivo" <gatilho_dispositivo>
                  | "sol" <gatilho_sol>
                  | "hora" <gatilho_hora>

<gatilho_estado> ::= <seletor_entidades> <de_estado_opt> "para" <valor_basico_ou_lista> <alias_gatilho_opt> <id_gatilho_opt> <duracao_gatilho_opt>

<de_estado_opt> ::= "de" <valor_basico_ou_lista>
                  | EPSILON

<gatilho_dispositivo> ::= <sujeito_dispositivo> <modo_dispositivo> <alias_gatilho_opt> <id_gatilho_opt> <duracao_gatilho_opt>

<modo_dispositivo> ::= "ligado"
                     | "desligado"
                     | "movimento"
                     | "aberto"
                     | "fechado"
                     | "nao_aberto"
                     | IDENT <comparador> <valor_basico>

<gatilho_sol> ::= <evento_sol> <alias_gatilho_opt> <id_gatilho_opt>
                | <evento_sol> "offset" STRING <alias_gatilho_opt> <id_gatilho_opt>

<gatilho_hora> ::= STRING <dias_opt> <alias_gatilho_opt> <id_gatilho_opt>

<alias_gatilho_opt> ::= "apelido" STRING
                      | EPSILON

<id_gatilho_opt> ::= "id" STRING
                   | EPSILON

<duracao_gatilho_opt> ::= "por" <valor_duracao>
                        | EPSILON

<dias_opt> ::= "dias" <lista_dias>
             | EPSILON

<lista_dias> ::= "[" <dia_semana> <lista_dias_tail_opt> "]"

<lista_dias_tail_opt> ::= "," <dia_semana> <lista_dias_tail_opt>
                        | EPSILON

<dia_semana> ::= "seg"
               | "ter"
               | "qua"
               | "qui"
               | "sex"
               | "sab"
               | "dom"

<evento_sol> ::= "nascer_do_sol"
               | "por_do_sol"

<comparador> ::= "acima"
               | "abaixo"
               | "igual"

<secao_condicoes_opt> ::= <secao_condicoes>
                        | EPSILON

<secao_condicoes> ::= "condicoes" "{" <lista_condicoes_opt> "}"

<lista_condicoes_opt> ::= <comando_condicao> <lista_condicoes_opt>
                        | EPSILON

<comando_condicao> ::= "se" <clausula_condicao> <habilitado_condicao_opt> ";"

<lista_entradas_condicao_opt> ::= <entrada_condicao> <lista_entradas_condicao_opt>
                                | EPSILON

<entrada_condicao> ::= <clausula_condicao> <habilitado_condicao_opt> ";"

<clausula_condicao> ::= <condicao_simples>
                      | <condicao_logica>

<condicao_simples> ::= <condicao_estado>
                     | <condicao_dispositivo>
                     | <condicao_gatilho>
                     | <condicao_horario>
                     | <condicao_sol>

<condicao_logica> ::= "qualquer" "{" <lista_entradas_condicao_opt> "}"
                    | "todos" "{" <lista_entradas_condicao_opt> "}"

<condicao_estado> ::= "estado" <ref_entidade> "igual" <valor_basico_ou_lista>

<condicao_dispositivo> ::= "dispositivo" <sujeito_dispositivo> <modo_condicao_dispositivo>

<modo_condicao_dispositivo> ::= "ligado"
                              | "desligado"
                              | "armado"
                              | "desarmado"
                              | "aberto"
                              | "fechado"
                              | IDENT <comparador> <valor_basico>

<condicao_gatilho> ::= "gatilho" "em" <seletor_ids_gatilho>

<condicao_horario> ::= "horario" <modo_condicao_horario>

<modo_condicao_horario> ::= "entre" STRING "e" STRING
                          | "depois" STRING <antes_horario_opt>
                          | "antes" STRING <depois_horario_opt>

<antes_horario_opt> ::= "antes" STRING
                      | EPSILON

<depois_horario_opt> ::= "depois" STRING
                       | EPSILON

<condicao_sol> ::= "sol" <modo_condicao_sol>

<modo_condicao_sol> ::= "antes" <evento_sol> <depois_sol_opt>
                      | "depois" <evento_sol> <antes_sol_opt>

<depois_sol_opt> ::= "depois" <evento_sol>
                   | EPSILON

<antes_sol_opt> ::= "antes" <evento_sol>
                  | EPSILON

<habilitado_condicao_opt> ::= "habilitado" BOOL
                            | EPSILON

<secao_acoes_opt> ::= <secao_acoes>
                    | EPSILON

<secao_acoes> ::= "acoes" "{" <lista_acoes_opt> "}"

<lista_acoes_opt> ::= <acao> <lista_acoes_opt>
                    | EPSILON

<acao> ::= <acao_simples>
         | <acao_em_bloco>

<acao_simples> ::= "faca" <comando_acao> <habilitado_acao_opt> ";"
                 | "espere" <valor_duracao> <habilitado_acao_opt> ";"

<acao_em_bloco> ::= <acao_se> <habilitado_acao_opt>
                  | <acao_escolha> <habilitado_acao_opt>

<comando_acao> ::= <acao_dispositivo>
                 | <acao_servico>

<acao_dispositivo> ::= <verbo_dispositivo> <sujeito_dispositivo>

<verbo_dispositivo> ::= "ligar"
                      | "desligar"
                      | "alternar"
                      | "abrir"
                      | "fechar"

<acao_servico> ::= "servico" QUALIFIED_NAME <alvo_opt> <dados_opt> <metadados_opt>

<alvo_opt> ::= "alvo" <bloco_alvo>
             | EPSILON

<dados_opt> ::= "dados" <mapa>
              | EPSILON

<metadados_opt> ::= "metadados" <mapa>
                  | EPSILON

<habilitado_acao_opt> ::= "habilitado" BOOL
                        | EPSILON

<acao_se> ::= "se" <clausula_condicao> "entao" <bloco_acoes> <senao_opt>

<senao_opt> ::= "senao" <bloco_acoes>
              | EPSILON

<bloco_acoes> ::= "{" <lista_acoes_opt> "}"

<acao_escolha> ::= "escolha" "{" <lista_casos_opt> "}"

<lista_casos_opt> ::= <caso_escolha> <lista_casos_opt>
                    | EPSILON

<caso_escolha> ::= "caso" <clausula_condicao> <bloco_acoes>

<bloco_alvo> ::= "{" <lista_alvos_opt> "}"

<lista_alvos_opt> ::= <entrada_alvo> <lista_alvos_opt>
                    | EPSILON

<entrada_alvo> ::= "entity_id" ":" <valor_entity_id> ";"
                 | "device_id" ":" <valor_device_id> ";"

<valor_entity_id> ::= <ref_entidade>
                    | <lista_entidades>

<valor_device_id> ::= STRING
                    | <lista_valores_basicos>

<mapa> ::= "{" <lista_campos_opt> "}"

<lista_campos_opt> ::= <campo> <lista_campos_opt>
                     | EPSILON

<campo> ::= <chave_mapa> ":" <valor> ";"

<chave_mapa> ::= IDENT
               | "device_id"
               | "entity_id"
               | "metadados"

<valor> ::= <valor_atomico>
          | <lista_valores>
          | <mapa>

<valor_atomico> ::= <valor_basico>
                  | <valor_duracao>

<valor_basico> ::= STRING
                 | NUMBER
                 | BOOL
                 | IDENT
                 | QUALIFIED_NAME

<valor_basico_ou_lista> ::= <valor_basico>
                          | <lista_valores_basicos>

<lista_valores_basicos> ::= "[" <valor_basico> <lista_valores_basicos_tail_opt> "]"

<lista_valores_basicos_tail_opt> ::= "," <valor_basico> <lista_valores_basicos_tail_opt>
                                   | EPSILON

<lista_valores> ::= "[" <valor> <lista_valores_tail_opt> "]"

<lista_valores_tail_opt> ::= "," <valor> <lista_valores_tail_opt>
                           | EPSILON

<seletor_ids_gatilho> ::= <id_gatilho_valor>
                        | <lista_ids_gatilho>

<lista_ids_gatilho> ::= "[" <id_gatilho_valor> <lista_ids_gatilho_tail_opt> "]"

<lista_ids_gatilho_tail_opt> ::= "," <id_gatilho_valor> <lista_ids_gatilho_tail_opt>
                               | EPSILON

<id_gatilho_valor> ::= STRING
                     | IDENT

<seletor_entidades> ::= <ref_entidade>
                      | <lista_entidades>

<lista_entidades> ::= "[" <ref_entidade> <lista_entidades_tail_opt> "]"

<lista_entidades_tail_opt> ::= "," <ref_entidade> <lista_entidades_tail_opt>
                             | EPSILON

<ref_entidade> ::= QUALIFIED_NAME
                 | IDENT

<sujeito_dispositivo> ::= IDENT <sujeito_dispositivo_tail>

<sujeito_dispositivo_tail> ::= "device_id" STRING "entity_id" STRING
                             | EPSILON

<valor_duracao> ::= DURATION
                  | STRING

<linhas_em_branco_opt> ::= NEWLINE <linhas_em_branco_opt>
                         | EPSILON
```

## Observacoes de projeto

### 1. Por que a linguagem usa secoes explicitas?

A estrutura:

```text
automacao "Nome" modo single {
    descricao "...";
    gatilhos { ... }
    condicoes { ... }
    acoes { ... }
}
```

reduz ambiguidade na analise sintatica. Cada secao comeca com uma palavra reservada diferente, o que facilita a construcao de uma tabela LL(1) sem depender de backtracking.

### 2. Por que existe o comando generico `faca servico ... alvo ... dados ... metadados ...`?

O YAML do professor usa muitos servicos distintos:

- `switch.turn_on`
- `switch.turn_off`
- `light.turn_on`
- `timer.start`
- `timer.finish`
- `automation.trigger`
- `notify.mobile_app_zfold4`
- `notify.send_message`
- `media_player.turn_off`
- `media_player.volume_set`
- `media_player.play_media`
- `tts.speak`
- `alexa_devices.send_text_command`
- `alexa_devices.send_sound`

Criar uma palavra reservada para cada integracao do Home Assistant deixaria a linguagem artificialmente grande e rigida. Por isso a gramatica define uma forma generica:

```text
faca servico QUALIFIED_NAME alvo { ... } dados { ... } metadados { ... };
```

Assim, a linguagem continua pequena e o compilador pode aceitar novas integracoes apenas reconhecendo o nome qualificado do servico.

### 3. Por que `dados` e `metadados` aceitam mapas e listas genericos?

Alguns servicos do YAML usam estruturas simples, como:

```text
dados { message: "Tablet carregando"; }
```

Outros usam dados aninhados, listas e objetos compostos, como em `media_player.play_media`. Por isso a gramatica aceita:

- valores escalares
- listas
- mapas aninhados

Isso evita prender a sintaxe a um servico especifico.

### 4. Por que `dispositivo` aceita tanto alias quanto forma inline?

A producao:

```text
<sujeito_dispositivo> ::= IDENT <sujeito_dispositivo_tail>
```

permite duas leituras:

- `IDENT device_id "..." entity_id "..."`: forma inline, como nos exemplos do enunciado.
- `IDENT`: referencia a um alias declarado antes com `dispositivo nome = ...;`

Essa escolha deixa a linguagem amigavel para uso rapido e tambem preparada para reutilizacao semantica.

### 5. Como a gramatica foi pensada para LL(1)?

- As secoes de uma automacao tem ordem fixa.
- Gatilhos sempre comecam por `quando`.
- Condicoes da secao `condicoes` sempre comecam por `se`.
- Acoes simples sempre comecam por `faca` ou `espere`.
- Blocos de controle usam palavras-chave exclusivas: `se ... entao ... senao` e `escolha ... caso ...`.
- Pontos potencialmente ambiguos foram fatorados, especialmente em gatilhos e no comando `faca`.

## Cobertura do YAML do professor

Com essa gramatica, a linguagem Homi consegue representar:

- `mode` com `single` e `restart`
- triggers `state`, `device`, `time` e `sun`
- campos opcionais como `id`, `apelido`, `offset` e `por`
- comparacoes `from`, `to`, `above`, `below` e listas de estados
- condicoes `state`, `device`, `trigger`, `time`, `sun`, `qualquer` e `todos`
- acoes por dispositivo
- acoes por servico com `alvo`, `dados` e `metadados`
- `delay`
- `if/then/else`
- `choose/case`
- `enabled` em condicoes e acoes

O que ainda fica para a fase semantica:

- validar dominios permitidos
- mapear `QUALIFIED_NAME` para automacoes e entidades reais do Home Assistant
- decidir quando um `IDENT` e alias declarado ou nome cru
- restringir quais campos fazem sentido para cada tipo de trigger, condicao ou servico
