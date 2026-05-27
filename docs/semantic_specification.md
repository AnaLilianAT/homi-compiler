# Especificacao Semantica

Depois que o parser constroi a AST, a analise semantica verifica se o programa Homi faz sentido antes da geracao de YAML.

## Tabela de simbolos

A tabela de simbolos em `src/symbol_table.py` armazena:

- entidades declaradas com nome simbolico, `entity_id` e dominio
- dispositivos declarados com nome simbolico, dominio, `device_id` e `entity_id`

O dominio pode ser inferido a partir do prefixo do `entity_id`, por exemplo:

- `light.sala` -> `light`
- `switch.luzes_da_sala` -> `switch`
- `timer.closet` -> `timer`

## Regras principais

### Entidades e dominios

- nomes simbolicos usados em `estado`, `target.entity_id` e referencias equivalentes precisam ter declaracao previa
- `DOTTED_ID` direto pode ser usado sem declaracao, desde que o dominio seja conhecido
- declaracoes duplicadas sao rejeitadas

### Automacoes

- `mode` deve ser `single` ou `restart`

### Triggers

- `state` precisa ter ao menos um `entity_id` e algum estado de origem ou destino
- `device` precisa de dominio, `device_id`, `entity_id` e tipo coerente
- triggers `bateria` e `volume_fluxo` exigem dominio `sensor` e limites numericos
- `sun` aceita apenas `sunrise` e `sunset`
- `time` exige horario valido no formato `HH:MM:SS`

### Conditions

- `state` exige entidade valida
- `device` exige dados completos do dispositivo
- `trigger` so pode referenciar ids definidos na mesma automacao
- `time` valida formato de horario
- `sun` valida eventos solares permitidos
- `qualquer` e `todos` propagam validacao para as subcondicoes

### Actions

- `ligar`, `desligar` e `alternar` so sao aceitos para dominios compativeis, como `light`, `switch` e `cover`
- `abrir` e `fechar` so sao aceitos para `cover`
- `timer.start` e `timer.finish` so podem mirar `timer.*`
- `automation.trigger` so pode mirar `automation.*`
- `media_player.turn_off`, `media_player.volume_set` e `media_player.play_media` exigem `media_player.*` ou `device_id`
- `notify.*` e `tts.speak` exigem carga textual em `dados`
- `alexa_devices.send_text_command` exige `device_id` e `text_command`
- `alexa_devices.send_sound` exige `device_id` e `sound`

## Diagnostics

Erros semanticos sao retornados como `Diagnostic` em `src/semantic.py`.

Quando a AST ainda nao carrega posicoes detalhadas, os diagnosticos usam uma posicao padrao. A infraestrutura ja esta organizada para incorporar linha e coluna mais precisas conforme o parser passar a preservar origem dos nos.

## Exemplos de erro semantico

Os exemplos em `examples/invalid_semantic/` foram preparados para demonstracao em apresentacao:

- `turn_on_sensor.homi`: tenta aplicar `ligar` em um dispositivo do dominio `sensor`
- `unknown_trigger_id.homi`: referencia um id de gatilho que nao existe na mesma automacao
- `wrong_cover_action.homi`: tenta `abrir` uma entidade que nao pertence ao dominio `cover`
- `wrong_timer_target.homi`: usa `timer.start` com alvo fora do dominio `timer`

Esses exemplos ajudam a mostrar a diferenca entre:

- erro sintatico: o programa nao respeita a forma da linguagem
- erro semantico: o programa respeita a forma, mas nao faz sentido dentro das regras do dominio
