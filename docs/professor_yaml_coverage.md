# Cobertura do YAML do Professor

Arquivo analisado: `examples/professor/automations_homi.yaml`

## Resumo

- Quantidade de automacoes: 24
- Aliases encontrados: 24
- Tipos de triggers encontrados: device (25), state (37), sun (3), time (4)
- Tipos de conditions encontrados: device (16), or (7), state (24), sun (2), time (4), trigger (40)
- Tipos de actions encontrados: choose (3), delay (14), if (41), service (65), type:close (1), type:open (1), type:toggle (1), type:turn_off (23), type:turn_on (15)
- Servicos chamados: alexa_devices.send_sound (1), alexa_devices.send_text_command (5), automation.trigger (3), light.turn_off (3), light.turn_on (1), media_player.play_media (2), media_player.turn_off (3), media_player.volume_set (2), notify.mobile_app_zfold4 (7), notify.send_message (1), switch.turn_off (18), switch.turn_on (8), timer.finish (1), timer.start (9), tts.speak (1)
- Dominios usados: alarm_control_panel (6), alexa_devices (6), automation (3), binary_sensor (7), cover (2), light (21), media_player (11), notify (8), sensor (5), switch (67), timer (10), tts (1)
- Modos usados: restart (8), single (16)
- Campos especiais encontrados: above (2), alias (29), below (3), brightness_pct (2), choose (3), data (65), delay (14), else (3), enabled (11), for (1), from (1), id (124), if (41), metadata (36), offset (3), target (52), then (82), to (36), weekday (1)

## Aliases

- Corda Corredor - movimento
- Por do Sol
- Tablet - carregador
- Nicole - LED da TV 
- Sala - desligar luzes NSPanel
- Closet - movimento 
- Lavabo - 3o botão interruptor
- Suite - botão Dani
- Sala - NSPanel controla painel LED TV
- Sala - movimento noturno 
- Corredor - chave hotel
- Suite - movimento
- Suite - ligar toalheiro 
- Nicole - movimento
- Eric -  movimento
- Corredor - movimento
- Sala - movimento
- Sala - subwoofer
- Sala - desligar LED sanca
- Sala - porta de entrada
- Aviso Sonoro - Interruptor Ligado
- Cozinha - desligar luzes
- Suíte - cortinas
- Suíte - escova Oral-B

## Cobertura por Padrao

- Automation alias: `automacao "Nome" modo ... { ... }`
- Automation description: `descricao "texto";`
- Automation mode single: `modo single`
- Automation mode restart: `modo restart`
- Automation id opaco: Nao modelado diretamente em Homi. O `id` opaco do Home Assistant e tratado como detalhe de persistencia, nao como construcao autoral da linguagem.
- Trigger state: `quando estado [entidade...] de ["..."] para ["..."] id "..." apelido "..." por 1min;`
- Trigger device on/off/motion/open: `quando dispositivo <dominio|alias> ... ligado|desligado|movimento|aberta|fechada ...;`
- Trigger battery: `quando dispositivo sensor ... bateria acima|abaixo N ...;`
- Trigger volume_flow: `quando dispositivo sensor ... volume_fluxo acima|abaixo N ...;`
- Trigger sun: `quando sol por_do_sol|nascer_do_sol offset "-00:45:00" id "..."`; 
- Trigger time: `quando hora "05:00:00" dias [seg, ter, ...] id "..."`; 
- Condition state: `se estado entidade igual ["estado"...];`
- Condition device: `se dispositivo <dominio|alias> ... ligado|desligado|armado|desarmado|aberto|fechado;`
- Condition trigger: `se gatilho em ["Id 1", "Id 2"];`
- Condition time: `se horario entre "01:00:00" e "06:30:00";`
- Condition sun: `se sol antes nascer_do_sol depois por_do_sol;`
- Condition logical or: `se qualquer { ...; ...; };`
- Condition logical and: `se todos { ...; ...; };`
- Action device: `faca ligar|desligar|alternar|abrir|fechar <dominio|alias> ...;`
- Action service: `faca servico dominio.servico alvo { ... } dados { ... } metadados { ... };`
- Action delay: `espere 1min45s;`
- Action if/then/else: `se <condicao> entao { ... } senao { ... }`
- Action choose/case: `escolha { caso <condicao> { ... } }`
- Field id: `id "Nome do gatilho";` e `gatilho em ["Nome do gatilho"]`
- Field alias: `apelido "Nome alternativo";`
- Field from: `de ["estado_origem"]` em trigger de estado
- Field to: `para ["estado_destino"]` em trigger de estado
- Field above: `bateria acima N` ou `volume_fluxo acima N`
- Field below: `bateria abaixo N` ou `volume_fluxo abaixo N`
- Field for: `por 1min` em triggers de estado ou dispositivo
- Field enabled: `habilitado true|false` em condicoes e acoes
- Field brightness_pct: `faca servico light.turn_on ... dados { brightness_pct: 20; };`
- Field weekday: `quando hora "05:00:00" dias [seg, ter, qua];`
- Field offset: `quando sol por_do_sol offset "-00:45:00";`
- Field choose: `escolha { caso ... { ... } }`
- Field if: `se ... entao { ... } senao { ... }`
- Field then: Bloco `entao { ... }` em `if`
- Field else: Bloco `senao { ... }` em `if`
- Field delay: `espere 45s;`
- Field target: `alvo { entity_id: [...]; device_id: [...]; }`
- Field data: `dados { chave: valor; ... }`
- Field metadata: `metadados { chave: valor; ... }`

## Exemplos Homi Equivalentes

- `examples/professor/homi_equivalents/01_state_trigger_delay_if_else.homi`
- `examples/professor/homi_equivalents/02_sun_trigger_choose_weather.homi`
- `examples/professor/homi_equivalents/03_battery_trigger_choose_notify.homi`
- `examples/professor/homi_equivalents/04_device_switch_mirror.homi`
- `examples/professor/homi_equivalents/05_time_trigger_media_actions.homi`
- `examples/professor/homi_equivalents/06_door_opened_for_notify.homi`
- `examples/professor/homi_equivalents/07_cover_open_close.homi`
- `examples/professor/homi_equivalents/08_timer_motion_restart.homi`

## Conclusao

Todos os padroes observados no YAML do professor foram analisados e receberam uma construcao Homi correspondente, com excecao do `id` opaco de automacao do Home Assistant, que foi explicitamente tratado como detalhe de persistencia e nao como parte autoral da linguagem.
