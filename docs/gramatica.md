# Gramática Livre de Contexto — Linguagem Homi

## Convenções de Notação

- Símbolos em `MAIÚSCULAS` → terminais (tokens produzidos pelo léxico)
- Símbolos em `minúsculas` → não-terminais
- `ε` → produção vazia (epsilon)
- `|` → alternativas de produção
- `//` → comentários explicativos (não fazem parte da gramática)

---

## Terminais (Tokens)

### Palavras Reservadas

| Token          | Lexema           | Descrição                              |
|----------------|------------------|----------------------------------------|
| `AUTOMACAO`    | `automacao`      | Início de uma automação                |
| `QUANDO`       | `quando`         | Seção de gatilhos                      |
| `SE`           | `se`             | Seção de condições ou ação condicional |
| `FACA`         | `faca`           | Seção de ações                         |
| `MODO`         | `modo`           | Seção de modo de execução              |
| `LIGAR`        | `ligar`          | Ação: ligar entidade                   |
| `DESLIGAR`     | `desligar`       | Ação: desligar entidade                |
| `AGUARDAR`     | `aguardar`       | Ação: esperar duração                  |
| `NOTIFICAR`    | `notificar`      | Ação: enviar notificação               |
| `PARA`         | `para`           | Preposição usada em notificações       |
| `ENTAO`        | `entao`          | Bloco então do condicional             |
| `SENAO`        | `senao`          | Bloco senão do condicional             |
| `FIM`          | `fim`            | Fechamento de bloco se/escolher        |
| `ESCOLHER`     | `escolher`       | Ação: bloco de escolhas (choose)       |
| `CASO`         | `caso`           | Alternativa dentro de escolher         |
| `ESTA`         | `esta`           | Verbo "está" — usado em condições      |
| `MUDA_PARA`    | `muda_para`      | Evento de mudança de estado            |
| `COMO`         | `como`           | Alias/ID do gatilho                    |
| `SENSOR`       | `sensor`         | Tipo de entidade: sensor binário       |
| `LUZ`          | `luz`            | Tipo de entidade: luz                  |
| `INTERRUPTOR`  | `interruptor`    | Tipo de entidade: switch               |
| `ALARME`       | `alarme`         | Tipo de entidade: painel de alarme     |
| `MEDIA`        | `media`          | Tipo de entidade: media player         |
| `TIMER`        | `timer`          | Tipo de entidade: timer                |
| `HORARIO`      | `horario`        | Keyword para condição/gatilho de hora  |
| `AO_HORARIO`   | `ao_horario`     | Gatilho de tempo exato                 |
| `ENTRE`        | `entre`          | Preposição para intervalo de horário   |
| `E`            | `e`              | Conjunção para intervalo de horário    |
| `NASCER_DO_SOL`| `nascer_do_sol`  | Gatilho: nascer do sol                 |
| `POR_DO_SOL`   | `por_do_sol`     | Gatilho: pôr do sol                    |
| `OFFSET`       | `offset`         | Deslocamento para gatilhos solares     |
| `BRILHO`       | `brilho`         | Parâmetro de brilho para luzes         |
| `UNICO`        | `unico`          | Modo: single                           |
| `REINICIAR`    | `reiniciar`      | Modo: restart                          |
| `FILA`         | `fila`           | Modo: queued                           |
| `PARALELO`     | `paralelo`       | Modo: parallel                         |

### Tokens de Estado

| Token        | Lexemas aceitos         | Descrição                       |
|--------------|-------------------------|---------------------------------|
| `ON`         | `on`                    | Estado ligado (inglês)          |
| `OFF`        | `off`                   | Estado desligado (inglês)       |
| `LIGADO`     | `ligado`                | Estado ligado (português)       |
| `DESLIGADO`  | `desligado`             | Estado desligado (português)    |
| `ARMADO`     | `armado`                | Estado armado (alarme)          |
| `DESARMADO`  | `desarmado`             | Estado desarmado (alarme)       |

### Tokens Literais

| Token       | Regex                                        | Exemplos                                |
|-------------|----------------------------------------------|-----------------------------------------|
| `ENTITY_ID` | `[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_.]*`       | `light.sala`, `binary_sensor.corredor`  |
| `TIME`      | `\d{2}:\d{2}(:\d{2})?`                       | `06:30`, `23:00:00`                     |
| `DURACAO`   | `\d+(ms\|s\|min\|h)`                         | `45s`, `4min`, `1h30`, `500ms`          |
| `NUMBER`    | `\d+(\.\d+)?`                                | `80`, `3.14`                            |
| `PORCENTO`  | `%`                                          | (usado após NUMBER em brilho)           |
| `STRING`    | `"[^"\n]*"\|'[^'\n]*'`                       | `"Corredor - movimento"`, `'Detectou'`  |

### Pontuação

| Token    | Lexema | Descrição              |
|----------|--------|------------------------|
| `LBRACE` | `{`    | Abre bloco automação   |
| `RBRACE` | `}`    | Fecha bloco automação  |
| `COLON`  | `:`    | Separador de seção     |

### Ignorados

| Padrão              | Ação                                     |
|---------------------|------------------------------------------|
| `//[^\n]*`          | Comentário de linha — descartado         |
| `[ \t\r]+`          | Espaços e tabulações — descartados       |
| `\n`                | Nova linha — descartado, `lineno += 1`   |

---

## Não-Terminais e Produções

### 1. Programa (raiz)

```
program
    : automation_list
    ;

automation_list
    : automation
    | automation_list automation
    ;
```

---

### 2. Automação

```
automation
    : AUTOMACAO STRING LBRACE body RBRACE
    ;

body
    : when_section
    | when_section se_section
    | when_section faca_section
    | when_section modo_section
    | when_section se_section faca_section
    | when_section se_section modo_section
    | when_section faca_section modo_section
    | when_section se_section faca_section modo_section
    ;
```

> `when_section` é obrigatória. As demais seções são opcionais e devem aparecer
> nesta ordem quando presentes: `quando → se → faca → modo`.

---

### 3. Seção `quando` (Gatilhos)

```
when_section
    : QUANDO COLON trigger_list
    ;

trigger_list
    : trigger
    | trigger_list trigger
    ;

trigger
    : entity_trigger
    | time_trigger
    | sun_trigger
    ;

entity_trigger
    : domain_kw ENTITY_ID MUDA_PARA state_value
    | domain_kw ENTITY_ID MUDA_PARA state_value COMO STRING
    ;

domain_kw
    : SENSOR
    | LUZ
    | INTERRUPTOR
    | ALARME
    | MEDIA
    | TIMER
    ;

time_trigger
    : AO_HORARIO TIME
    | AO_HORARIO TIME COMO STRING
    ;

sun_trigger
    : POR_DO_SOL
    | POR_DO_SOL COMO STRING
    | POR_DO_SOL OFFSET DURACAO
    | POR_DO_SOL OFFSET DURACAO COMO STRING
    | NASCER_DO_SOL
    | NASCER_DO_SOL COMO STRING
    | NASCER_DO_SOL OFFSET DURACAO
    | NASCER_DO_SOL OFFSET DURACAO COMO STRING
    ;
```

---

### 4. Seção `se` (Condições globais)

```
se_section
    : SE COLON condition_list
    ;

condition_list
    : condition
    | condition_list condition
    ;

condition
    : ENTITY_ID ESTA state_value
    | domain_kw ENTITY_ID ESTA state_value   // forma legível: "luz light.x esta desligada"
    | HORARIO ENTRE TIME E TIME
    ;
```

---

### 5. Seção `faca` (Ações)

```
faca_section
    : FACA COLON action_list
    ;

action_list
    : action
    | action_list action
    ;

action
    : LIGAR ENTITY_ID
    | LIGAR ENTITY_ID BRILHO NUMBER PORCENTO
    | DESLIGAR ENTITY_ID
    | AGUARDAR DURACAO
    | NOTIFICAR STRING PARA ENTITY_ID
    | if_action
    | escolher_action
    ;

if_action
    : SE condition_list ENTAO COLON action_list FIM
    | SE condition_list ENTAO COLON action_list SENAO COLON action_list FIM
    ;

escolher_action
    : ESCOLHER COLON choice_list FIM
    ;

choice_list
    : choice
    | choice_list choice
    ;

choice
    : CASO condition_list FACA COLON action_list
    ;
```

---

### 6. Seção `modo`

```
modo_section
    : MODO COLON modo_value
    ;

modo_value
    : UNICO
    | REINICIAR
    | FILA
    | PARALELO
    ;
```

---

### 7. Valor de Estado

```
state_value
    : ON
    | OFF
    | LIGADO
    | DESLIGADO
    | ARMADO
    | DESARMADO
    | STRING
    | NUMBER
    ;
```

> Aceitar `STRING` e `NUMBER` como estado permite cobrir valores genéricos como
> `"charging"`, `"idle"`, `"playing"`, `1`, etc., usados em sensores e media players.

---

## Exemplo Completo Anotado

```homi
// Cada token está marcado com [TIPO]

automacao [AUTOMACAO] "Corredor - movimento" [STRING] { [LBRACE]

  quando [QUANDO] : [COLON]
    sensor [SENSOR] binary_sensor.motion_sensor_movimento [ENTITY_ID]
      muda_para [MUDA_PARA] on [ON]
      como [COMO] "Detectou" [STRING]

  se [SE] : [COLON]
    alarm_control_panel.alarmo [ENTITY_ID] esta [ESTA] desarmado [DESARMADO]
    light.corda_led_corredor [ENTITY_ID] esta [ESTA] desligado [DESLIGADO]

  faca [FACA] : [COLON]
    ligar [LIGAR] light.corda_led_corredor [ENTITY_ID]

    se [SE]
      horario [HORARIO] entre [ENTRE] 01:15 [TIME] e [E] 12:00 [TIME]
    entao [ENTAO] : [COLON]
      aguardar [AGUARDAR] 45s [DURACAO]
    senao [SENAO] : [COLON]
      aguardar [AGUARDAR] 1min [DURACAO]
    fim [FIM]

    desligar [DESLIGAR] light.corda_led_corredor [ENTITY_ID]

  modo [MODO] : [COLON] reiniciar [REINICIAR]

} [RBRACE]
```

---

## Mapeamento Homi → YAML (Home Assistant)

| Construção Homi                          | YAML gerado                                              |
|------------------------------------------|----------------------------------------------------------|
| `automacao "Nome" { ... }`               | `- alias: Nome`                                          |
| `sensor X muda_para on como "ID"`        | `trigger: state`, `entity_id: X`, `to: 'on'`, `id: ID`  |
| `ao_horario 05:00`                       | `trigger: time`, `at: '05:00:00'`                        |
| `por_do_sol offset -1h30 como "chuva"`   | `trigger: sun`, `event: sunset`, `offset: '-01:30:00'`   |
| `X esta desarmado`                       | `condition: state`, `entity_id: X`, `state: disarmed`    |
| `horario entre 01:00 e 06:30`            | `condition: time`, `after: '01:00:00'`, `before: '06:30:00'` |
| `ligar light.X`                          | `action: light.turn_on`, `target: {entity_id: X}`        |
| `ligar light.X brilho 50%`              | `action: light.turn_on`, `data: {brightness_pct: 50}`    |
| `desligar switch.X`                      | `action: switch.turn_off`, `target: {entity_id: X}`      |
| `aguardar 45s`                           | `delay: {seconds: 45}`                                   |
| `aguardar 4min`                          | `delay: {minutes: 4}`                                    |
| `notificar "msg" para notify.X`          | `action: notify.X`, `data: {message: msg}`               |
| `se ... entao: ... fim`                  | `if: [...]`, `then: [...]`                               |
| `se ... entao: ... senao: ... fim`       | `if: [...]`, `then: [...]`, `else: [...]`                |
| `escolher: caso ... faca: ... fim`       | `choose: [{conditions: [...], sequence: [...]}]`         |
| `modo: unico`                            | `mode: single`                                           |
| `modo: reiniciar`                        | `mode: restart`                                          |
| `modo: fila`                             | `mode: queued`                                           |
| `modo: paralelo`                         | `mode: parallel`                                         |

---

## Regras Semânticas (resumo)

| Regra                                  | Erro gerado                                                        |
|----------------------------------------|--------------------------------------------------------------------|
| Entidade com domínio desconhecido      | `domínio 'X' não reconhecido`                                      |
| `brilho` em não-luz                    | `'brilho' só pode ser usado com domínio 'light'`                   |
| `notificar ... para` em não-notify     | `entidade alvo de 'notificar' deve ter domínio 'notify'`           |
| Estado inválido para o domínio         | `estado 'X' inválido para domínio 'Y'`                             |
| Duração ≤ 0                            | `duração deve ser positiva`                                        |
| Dois `automacao` com o mesmo nome      | `[aviso] nome de automação duplicado: 'X'`                         |
