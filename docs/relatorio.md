# Relatório Técnico — Compilador Homi

**Disciplina:** Compiladores  
**Entrega:** 06/06/2026  
**Descrição:** Compilador (tradutor) que converte scripts da linguagem **Homi** em arquivos YAML compatíveis com o Home Assistant.

---

## 1. Visão Geral

A linguagem **Homi** permite que usuários leigos descrevam automações residenciais em português estruturado. O compilador percorre quatro fases clássicas:

```
arquivo.homi
    │
    ▼
[Fase 1] Análise Léxica     lexer.py    — PLY lex  (DFA automático)
    │
    ▼
[Fase 2] Análise Sintática  parser.py   — PLY yacc (tabela LALR(1))
    │ AST
    ▼
[Fase 3] Análise Semântica  semantic.py — tabela de símbolos + checagem de tipos
    │ AST validada
    ▼
[Fase 4] Geração de Código  codegen.py  — AST → YAML Home Assistant
    │
    ▼
arquivo.yaml
```

---

## 2. Definição da Linguagem Homi

### 2.1 Princípios de Design

- Palavras-chave em **português** para acessibilidade a usuários leigos.
- Estrutura declarativa com seções claramente separadas (`quando`, `se`, `faca`, `modo`).
- Formas **masculina e feminina** aceitas nos estados (`desligado`/`desligada`, `armado`/`armada`).
- Estados em inglês (`on`, `off`) também aceitos para compatibilidade com o HA.

### 2.2 Estrutura de um Script Homi

```homi
// Comentário de linha

automacao "Nome da automacao" {

  quando:                          // gatilhos (obrigatório)
    sensor binary_sensor.x muda_para on como "ID"
    ao_horario 07:30
    por_do_sol offset -45min como "sol"

  se:                              // condições globais (opcional)
    switch.luz esta desligado
    horario entre 23:00 e 06:00

  faca:                            // ações (opcional)
    ligar light.sala brilho 80%
    aguardar 2min
    desligar light.sala
    notificar "Movimento!" para notify.mobile_app_zfold4
    se
      switch.x esta ligado
    entao:
      ligar light.y
    senao:
      desligar light.y
    fim
    escolher:
      caso switch.a esta desligado faca:
        ligar switch.a
    fim

  modo: reiniciar                  // single | restart | queued | parallel
}
```

---

## 3. Especificação da GLC (Gramática Livre de Contexto)

### 3.1 Terminais

#### Palavras Reservadas

| Token | Lexema | Significado |
|---|---|---|
| `AUTOMACAO` | `automacao` | Declaração de automação |
| `QUANDO` | `quando` | Seção de gatilhos |
| `SE` | `se` | Seção de condições ou ação condicional |
| `FACA` | `faca` | Seção de ações |
| `MODO` | `modo` | Modo de execução |
| `LIGAR` | `ligar` | Ação: ligar entidade |
| `DESLIGAR` | `desligar` | Ação: desligar entidade |
| `AGUARDAR` | `aguardar` | Ação: aguardar tempo |
| `NOTIFICAR` | `notificar` | Ação: enviar notificação |
| `PARA` | `para` | Preposição (alvo de notificação) |
| `ENTAO` | `entao` | Bloco then |
| `SENAO` | `senao` | Bloco else |
| `FIM` | `fim` | Fecha bloco se / escolher |
| `ESCOLHER` | `escolher` | Ação: escolha múltipla |
| `CASO` | `caso` | Alternativa dentro de escolher |
| `ESTA` | `esta` | Predicado "está" (condições) |
| `MUDA_PARA` | `muda_para` | Evento de mudança de estado |
| `COMO` | `como` | Define ID do gatilho |
| `SENSOR` | `sensor` | Tipo: sensor binário |
| `LUZ` | `luz` | Tipo: luz |
| `INTERRUPTOR` | `interruptor` | Tipo: switch |
| `ALARME` | `alarme` | Tipo: painel de alarme |
| `MEDIA` | `media` | Tipo: media player |
| `TIMER` | `timer` | Tipo: timer |
| `HORARIO` | `horario` | Keyword de tempo |
| `AO_HORARIO` | `ao_horario` | Gatilho de horário exato |
| `ENTRE` | `entre` | Intervalo de tempo |
| `E` | `e` | Conjunção de intervalo |
| `NASCER_DO_SOL` | `nascer_do_sol` | Gatilho: sunrise |
| `POR_DO_SOL` | `por_do_sol` | Gatilho: sunset |
| `OFFSET` | `offset` | Deslocamento solar |
| `BRILHO` | `brilho` | Parâmetro de brilho |
| `UNICO` | `unico` | Modo single |
| `REINICIAR` | `reiniciar` | Modo restart |
| `FILA` | `fila` | Modo queued |
| `PARALELO` | `paralelo` | Modo parallel |
| `ON` / `OFF` | `on` / `off` | Estados inglês |
| `LIGADO` / `LIGADA` | `ligado` / `ligada` | Estado ligado PT |
| `DESLIGADO` / `DESLIGADA` | `desligado` / `desligada` | Estado desligado PT |
| `ARMADO` / `ARMADA` | `armado` / `armada` | Estado armado PT |
| `DESARMADO` / `DESARMADA` | `desarmado` / `desarmada` | Estado desarmado PT |

#### Tokens Literais

| Token | Expressão Regular | Exemplos |
|---|---|---|
| `ENTITY_ID` | `[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_.]*` | `light.sala`, `binary_sensor.corredor` |
| `TIME` | `\d{2}:\d{2}(:\d{2})?` | `06:30`, `23:00:00` |
| `DURACAO` | `-?\d+h\d+\|-?\d+(?:ms\|s\|min\|h)` | `45s`, `4min`, `-1h30`, `-45min` |
| `NUMBER` | `\d+(\.\d+)?` | `80`, `3.14` |
| `PORCENTO` | `%` | `%` |
| `STRING` | `"[^"\n]*"\|'[^'\n]*'` | `"Movimento detectado"` |
| `LBRACE` | `\{` | `{` |
| `RBRACE` | `\}` | `}` |
| `COLON` | `:` | `:` |

### 3.2 Não-Terminais e Produções

```
program
    : automation_list

automation_list
    : automation
    | automation_list automation

automation
    : AUTOMACAO STRING LBRACE body RBRACE

body
    : when_section opt_se_section opt_faca_section opt_modo_section

when_section
    : QUANDO COLON trigger_list

trigger_list
    : trigger
    | trigger_list trigger

trigger
    : domain_kw ENTITY_ID MUDA_PARA state_value
    | domain_kw ENTITY_ID MUDA_PARA state_value COMO STRING
    | AO_HORARIO TIME
    | AO_HORARIO TIME COMO STRING
    | POR_DO_SOL
    | POR_DO_SOL COMO STRING
    | POR_DO_SOL OFFSET DURACAO
    | POR_DO_SOL OFFSET DURACAO COMO STRING
    | NASCER_DO_SOL
    | NASCER_DO_SOL COMO STRING
    | NASCER_DO_SOL OFFSET DURACAO
    | NASCER_DO_SOL OFFSET DURACAO COMO STRING

domain_kw
    : SENSOR | LUZ | INTERRUPTOR | ALARME | MEDIA | TIMER

opt_se_section
    : se_section | ε

se_section
    : SE COLON condition_list

condition_list
    : condition
    | condition_list condition

condition
    : ENTITY_ID ESTA state_value
    | domain_kw ENTITY_ID ESTA state_value
    | HORARIO ENTRE TIME E TIME

opt_faca_section
    : faca_section | ε

faca_section
    : FACA COLON action_list

action_list
    : action
    | action_list action

action
    : LIGAR ENTITY_ID
    | LIGAR ENTITY_ID BRILHO NUMBER PORCENTO
    | DESLIGAR ENTITY_ID
    | AGUARDAR DURACAO
    | NOTIFICAR STRING PARA ENTITY_ID
    | SE condition_list ENTAO COLON action_list FIM
    | SE condition_list ENTAO COLON action_list SENAO COLON action_list FIM
    | ESCOLHER COLON choice_list FIM

choice_list
    : choice
    | choice_list choice

choice
    : CASO condition_list FACA COLON action_list

opt_modo_section
    : modo_section | ε

modo_section
    : MODO COLON modo_value

modo_value
    : UNICO | REINICIAR | FILA | PARALELO

state_value
    : ON | OFF | LIGADO | DESLIGADO | ARMADO | DESARMADO | STRING | NUMBER
```

---

## 4. Especificação do Analisador Léxico

### 4.1 Implementação

Implementado com **PLY lex**, que gera um DFA (Autômato Finito Determinístico) automaticamente a partir das expressões regulares definidas nas funções `t_*`.

Arquivo: `lexer.py` | Função de fábrica: `build_lexer()`

### 4.2 Prioridade dos Tokens

Em PLY, funções-token têm prioridade sobre strings-token. Funções são tentadas na ordem de definição. A ordem usada é:

1. `t_ENTITY_ID` — testado **antes** de `t_ID` para que `light.sala` seja um único token
2. `t_DURACAO` — testado **antes** de `t_NUMBER` para que `45s` não vire `45` + erro
3. `t_TIME` — testado **antes** de `t_COLON` para que `01:15` não vire `01` + `:` + `15`
4. `t_NUMBER`
5. `t_STRING`
6. `t_ID` — identifica palavras reservadas via dicionário `reserved`

### 4.3 Tratamento de Comentários e Linhas

```python
def t_COMMENT(t):
    r'//[^\n]*'
    pass   # descartado

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
```

### 4.4 Tratamento de Erros Léxicos

Dois pontos de detecção:

- **`t_error(t)`**: caractere isolado inválido (ex: `@`, `#`). Registra o erro, avança 1 caractere e continua.
- **`t_ID`**: identificador sem ponto não encontrado no dicionário `reserved`. Registra o erro e descarta o token.

Todos os erros são acumulados em `lexer.lex_errors` para exibição consolidada.

---

## 5. Especificação do Analisador Sintático

### 5.1 Método: LALR(1)

Implementado com **PLY yacc**, que constrói a tabela LALR(1) automaticamente a partir das funções `p_*`.

Arquivo: `parser.py` | Tabela gerada: `parsetab.py`

### 5.2 Construção da AST

Cada produção constrói nós da AST (definidos em `ast_nodes.py`):

| Produção | Nó gerado |
|---|---|
| `automation` | `AutomationNode(name, triggers, conditions, actions, mode)` |
| `trigger` | `TriggerNode(kind, entity, to, at, sun_event, offset, trigger_id)` |
| `condition` | `ConditionNode(kind, entity, state, after, before)` |
| `action` | `ActionNode(kind, entity, duration, message, brightness, ...)` |
| `choice` | `ChoiceNode(conditions, actions)` |

### 5.3 Conflitos Shift-Reduce

A gramática possui conflitos shift-reduce esperados em produções com sufixos opcionais (ex: `COMO STRING`, `BRILHO NUMBER PORCENTO`, `OFFSET DURACAO`). Em todos os casos, o comportamento padrão do PLY — **preferir shift** — produz o resultado correto (match mais longo).

Nenhum conflito reduce-reduce foi detectado.

### 5.4 Recuperação de Erros — Modo Pânico

O parser **não aborta** no primeiro erro. São definidas três produções de recuperação:

```python
# Sincronização em trigger_list, condition_list e action_list
trigger_list   : trigger_list   error trigger
condition_list : condition_list error condition
action_list    : action_list    error action
```

Quando um token inválido é encontrado numa lista, o PLY descarta tokens até encontrar algo que case com o próximo item, permitindo que o resto do arquivo seja analisado.

---

## 6. Especificação do Analisador Semântico

### 6.1 Tabela de Símbolos

Implementada em `SymbolTable` (dentro de `semantic.py`). Mapeia o prefixo de cada `entity_id` (o domínio HA) para um tipo semântico Homi:

| Domínio HA | Tipo Homi |
|---|---|
| `light` | `luz` |
| `switch`, `input_boolean`, `fan` | `interruptor` |
| `binary_sensor`, `sensor`, `weather`, `climate` | `sensor` |
| `alarm_control_panel` | `alarme` |
| `timer` | `timer` |
| `media_player` | `media` |
| `cover` | `cortina` |
| `notify` | `notificacao` |
| `automation` | `automacao` |

### 6.2 Regras de Verificação

| # | Regra | Exemplo de erro |
|---|---|---|
| 1 | Domínio do `entity_id` deve existir na tabela | `xyz.sensor esta on` |
| 2 | Estados exclusivos de alarme (`disarmed`, `armed_*`) só em `alarm_control_panel` | `luz light.sala esta desarmada` |
| 3 | `brilho` exclusivo do domínio `light` | `ligar switch.sala brilho 80%` |
| 4 | Alvo de `notificar` deve ser `notify.*` | `notificar "msg" para light.sala` |
| 5 | Duração de `aguardar` não pode ser negativa | `aguardar -5s` |
| 6 | Nome de automação duplicado (aviso, não erro) | `automacao "X" { ... } automacao "X" { ... }` |

### 6.3 Normalização de Estados

O parser normaliza estados PT → valores HA durante a análise sintática:

| Lexema Homi | Valor HA |
|---|---|
| `ligado`, `ligada`, `on` | `on` |
| `desligado`, `desligada`, `off` | `off` |
| `armado`, `armada` | `armed_home` |
| `desarmado`, `desarmada` | `disarmed` |

---

## 7. Geração de Código Intermediário (YAML)

### 7.1 Mapeamento AST → YAML

| Construção Homi | YAML Home Assistant |
|---|---|
| `automacao "Nome" { ... }` | `- alias: Nome` |
| `sensor X muda_para on como "ID"` | `trigger: state`, `entity_id: X`, `to: 'on'`, `id: ID` |
| `ao_horario 05:00` | `trigger: time`, `at: '05:00:00'` |
| `por_do_sol offset -1h30 como "chuva"` | `trigger: sun`, `event: sunset`, `offset: '-01:30:00'`, `id: chuva` |
| `X esta desarmado` | `condition: state`, `entity_id: X`, `state: disarmed` |
| `horario entre 01:00 e 06:30` | `condition: time`, `after: '01:00:00'`, `before: '06:30:00'` |
| `ligar light.X` | `action: light.turn_on`, `target: {entity_id: X}` |
| `ligar light.X brilho 50%` | `action: light.turn_on`, `data: {brightness_pct: 50}` |
| `desligar switch.X` | `action: switch.turn_off`, `target: {entity_id: X}` |
| `aguardar 45s` | `delay: {seconds: 45}` |
| `aguardar 4min` | `delay: {minutes: 4}` |
| `aguardar 1h30` | `delay: {hours: 1, minutes: 30}` |
| `notificar "msg" para notify.X` | `action: notify.X`, `data: {message: msg}` |
| `se ... entao: ... fim` | `if: [...]`, `then: [...]` |
| `se ... entao: ... senao: ... fim` | `if: [...]`, `then: [...]`, `else: [...]` |
| `escolher: caso ... faca: ... fim` | `choose: [{conditions: [...], sequence: [...]}]` |
| `modo: unico` | `mode: single` |
| `modo: reiniciar` | `mode: restart` |

### 7.2 Tratamento de Indentação YAML

É utilizado o **PyYAML** com um `Dumper` customizado (`_HomiDumper`) que força aspas simples em strings que o YAML padrão converteria para booleanos (`on`, `off`, `true`, `false`) ou interpretaria incorretamente (horários `HH:MM:SS`, offsets `-01:30:00`).

---

## 8. Exemplos de Scripts Homi e YAMLs Resultantes

### Exemplo 1 — Luz por movimento com lógica de horário

**Entrada (`corredor_movimento.homi`):**
```homi
automacao "Corredor - movimento" {
  quando:
    sensor binary_sensor.motion_sensor_movimento muda_para on como "Detectou"
    sensor binary_sensor.corredor_suite_luminance_motion_sensor_movimento muda_para on como "Detectou2"
    sensor binary_sensor.tz3000_6ygjfyll_ts0202 muda_para on como "Detectou3"

  se:
    alarme alarm_control_panel.alarmo esta desarmado
    luz light.corda_led_corredor esta desligada

  faca:
    ligar light.corda_led_corredor
    se
      horario entre 01:15 e 12:00
    entao:
      aguardar 45s
    senao:
      aguardar 1min
    fim
    desligar light.corda_led_corredor

  modo: reiniciar
}
```

**Saída (`corredor_movimento.yaml`):**
```yaml
- alias: Corredor - movimento
  triggers:
  - trigger: state
    entity_id: binary_sensor.motion_sensor_movimento
    to: 'on'
    id: Detectou
  - trigger: state
    entity_id: binary_sensor.corredor_suite_luminance_motion_sensor_movimento
    to: 'on'
    id: Detectou2
  - trigger: state
    entity_id: binary_sensor.tz3000_6ygjfyll_ts0202
    to: 'on'
    id: Detectou3
  conditions:
  - condition: state
    entity_id: alarm_control_panel.alarmo
    state: disarmed
  - condition: state
    entity_id: light.corda_led_corredor
    state: 'off'
  actions:
  - action: light.turn_on
    target:
      entity_id: light.corda_led_corredor
  - if:
    - condition: time
      after: '01:15:00'
      before: '12:00:00'
    then:
    - delay:
        seconds: 45
    else:
    - delay:
        minutes: 1
  - action: light.turn_off
    target:
      entity_id: light.corda_led_corredor
  mode: restart
```

---

### Exemplo 2 — Gatilho solar com múltiplas escolhas

**Entrada (`por_do_sol.homi`):**
```homi
automacao "Por do Sol" {
  quando:
    por_do_sol offset -1h30 como "chuva"
    por_do_sol offset -1h15 como "nublado"
    por_do_sol offset -45min como "sol"

  se:
    alarme alarm_control_panel.alarmo esta desarmado

  faca:
    escolher:
      caso
        interruptor switch.luzes_da_cozinha esta desligado
      faca:
        ligar switch.luzes_da_cozinha
    caso
        interruptor switch.luzes_da_sala esta desligado
      faca:
        ligar switch.luzes_da_sala
    fim

  modo: unico
}
```

**Saída (`por_do_sol.yaml`):**
```yaml
- alias: Por do Sol
  triggers:
  - trigger: sun
    event: sunset
    offset: '-01:30:00'
    id: chuva
  - trigger: sun
    event: sunset
    offset: '-01:15:00'
    id: nublado
  - trigger: sun
    event: sunset
    offset: '-00:45:00'
    id: sol
  conditions:
  - condition: state
    entity_id: alarm_control_panel.alarmo
    state: disarmed
  actions:
  - choose:
    - conditions:
      - condition: state
        entity_id: switch.luzes_da_cozinha
        state: 'off'
      sequence:
      - action: switch.turn_on
        target:
          entity_id: switch.luzes_da_cozinha
    - conditions:
      - condition: state
        entity_id: switch.luzes_da_sala
        state: 'off'
      sequence:
      - action: switch.turn_on
        target:
          entity_id: switch.luzes_da_sala
  mode: single
```

---

### Exemplo 3 — Detecção de Erros

**Script com erro semântico (`erro_semantico.homi`):**
```homi
automacao "Erro de tipo - brilho em switch" {
  quando:
    sensor binary_sensor.motion muda_para on
  faca:
    ligar switch.luzes_da_sala brilho 80%   // ERRO: brilho só em 'light'
  modo: unico
}

automacao "Erro de tipo - notificar para luz" {
  quando:
    sensor binary_sensor.motion muda_para on
  faca:
    notificar "msg" para light.sala          // ERRO: alvo deve ser notify.*
  modo: unico
}

automacao "Erro de estado - luz desarmada" {
  quando:
    sensor binary_sensor.motion muda_para on
  se:
    luz light.sala esta desarmado            // ERRO: 'disarmed' só em alarme
  faca:
    ligar light.sala
  modo: unico
}
```

**Saída do compilador:**
```
Erro semântico [linha 9]  'brilho' só pode ser usado com domínio 'light'; 'switch.luzes_da_sala' pertence ao domínio 'switch'
Erro semântico [linha 22] o alvo de 'notificar' deve ter domínio 'notify'; recebido: 'light.sala' (domínio: 'light')
Erro semântico [linha 35] estado 'disarmed' é válido apenas para 'alarm_control_panel'; 'light.sala' tem domínio 'light'

Compilação interrompida: 3 erro(s) semântico(s).
```

---

## 9. Estrutura do Repositório

```
homi_compiler/
├── Makefile                     # targets: run, test, clean, install
├── homi.py                      # ponto de entrada (CLI)
├── lexer.py                     # análise léxica (PLY lex)
├── parser.py                    # análise sintática (PLY yacc, LALR(1))
├── ast_nodes.py                 # nós da AST (dataclasses)
├── semantic.py                  # análise semântica + tabela de símbolos
├── codegen.py                   # geração de código YAML
├── errors.py                    # classes de erro (ErroLexico, ErroSintatico, ErroSemantico)
├── parsetab.py                  # tabela LALR(1) gerada automaticamente pelo PLY
├── docs/
│   ├── gramatica.md             # GLC completa com notação formal
│   └── relatorio.md             # este documento
└── tests/
    ├── exemplos_validos/
    │   ├── corredor_movimento.homi / .yaml
    │   ├── sala_noturna.homi / .yaml
    │   └── por_do_sol.homi / .yaml
    └── exemplos_invalidos/
        ├── erro_lexico.homi
        ├── erro_sintatico.homi
        └── erro_semantico.homi
```

## 10. Instruções de Compilação e Execução

```bash
# Instalar dependências
make install          # ou:  pip install ply pyyaml pytest

# Compilar um arquivo .homi
make run FILE=tests/exemplos_validos/corredor_movimento.homi

# Equivalente direto
python homi.py tests/exemplos_validos/corredor_movimento.homi

# Especificar arquivo de saída
python homi.py minha_automacao.homi -o resultado.yaml

# Verificar erros sem gerar saída
python homi.py minha_automacao.homi --check

# Inspecionar a AST
python homi.py minha_automacao.homi --ast

# Rodar testes
make test
```
