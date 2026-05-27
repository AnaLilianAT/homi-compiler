# Mapeamento Homi -> YAML

O gerador em `src/yaml_generator.py` traduz a AST validada da linguagem Homi para uma lista de automacoes no formato esperado pelo Home Assistant.

## Automacao

| Homi | YAML |
| --- | --- |
| `automacao "Nome" modo restart { ... }` | `- alias: Nome`<br>`  description: ...`<br>`  triggers: [...]`<br>`  conditions: [...]`<br>`  actions: [...]`<br>`  mode: restart` |

## Triggers

| Homi | YAML |
| --- | --- |
| `quando estado [binary_sensor.a, binary_sensor.b] para ["on"] id "Movimento";` | `trigger: state` + `entity_id`, `to`, `id` |
| `quando dispositivo switch device_id "abc" entity_id "def" ligado id "Liga";` | `trigger: device` + `domain`, `device_id`, `entity_id`, `type: turned_on`, `id` |
| `quando dispositivo sensor device_id "abc" entity_id "def" bateria abaixo 20;` | `type: battery_level` + `below: 20` |
| `quando dispositivo sensor device_id "abc" entity_id "def" bateria acima 20;` | `type: battery_level` + `above: 20` |
| `quando dispositivo sensor device_id "abc" entity_id "def" volume_fluxo acima 3.5;` | `type: volume_flow_rate` + `above: 3.5` |
| `quando sol por_do_sol offset "-00:45:00" id "sol";` | `trigger: sun`, `event: sunset`, `offset`, `id` |
| `quando hora "05:00:00" id "Hora";` | `trigger: time`, `at`, `id` |

### Mapeamento de tipos de trigger de dispositivo

| Homi | YAML |
| --- | --- |
| `ligado` | `turned_on` |
| `desligado` | `turned_off` |
| `movimento` | `motion` |
| `aberta` | `opened` |
| `fechada` | `not_opened` |

## Conditions

| AST Homi | YAML |
| --- | --- |
| `StateCondition` | `condition: state` |
| `DeviceCondition` | `condition: device` |
| `TriggerCondition` | `condition: trigger` |
| `TimeCondition` | `condition: time` |
| `SunCondition` | `condition: sun` |
| `LogicalCondition(operator="or")` | `condition: or` + `conditions` |
| `LogicalCondition(operator="and")` | `condition: and` + `conditions` |

## Actions

| Homi | YAML |
| --- | --- |
| `faca ligar light device_id "abc" entity_id "def";` | `type: turn_on`, `device_id: abc`, `entity_id: def`, `domain: light` |
| `faca servico switch.turn_on alvo { entity_id: [switch.a]; } dados {};` | `action: switch.turn_on`, `target`, `data` |
| `espere 1min45s;` | `delay: { hours: 0, minutes: 1, seconds: 45, milliseconds: 0 }` |
| `se <condicao> entao { ... } senao { ... }` | `if`, `then`, `else` |
| `escolha { caso <condicao> { ... } }` | `choose` com itens contendo `conditions` e `sequence` |

### Mapeamento de tipos de acao de dispositivo

| Homi | YAML |
| --- | --- |
| `ligar` | `turn_on` |
| `desligar` | `turn_off` |
| `alternar` | `toggle` |
| `abrir` | `open` |
| `fechar` | `close` |

## Observacoes

- A saida final e uma lista YAML de automacoes.
- `entity_id` e `device_id` sao preservados como listas quando a AST traz multiplos alvos.
- A serializacao usa `PyYAML` com `allow_unicode=True`.
- O gerador valida o YAML produzido usando `yaml.safe_load` antes de retornar o texto final.
