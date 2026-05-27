# Relatorio Tecnico do Projeto Homi-Compiler

## 1. Introducao

O Home Assistant utiliza arquivos YAML para descrever automacoes residenciais. Embora esse formato seja flexivel e amplamente usado, ele pode se tornar verboso, repetitivo e pouco intuitivo para usuarios leigos, especialmente quando uma automacao envolve multiplos gatilhos, condicoes logicas, atrasos, servicos e estruturas aninhadas como `if` e `choose`.

Este projeto propoe a linguagem Homi como uma camada de abstracao sobre o YAML do Home Assistant. A ideia central e permitir que automacoes residenciais sejam escritas em uma sintaxe mais declarativa, legivel e proxima do dominio do problema, reduzindo o custo cognitivo de edicao manual de YAML.

Do ponto de vista de Compiladores, o fluxo implementado no projeto segue as etapas classicas do front-end e parte do back-end:

```text
Homi -> Scanner -> Parser LL(1) -> AST -> Analise Semantica -> YAML
```

O codigo fonte em Homi e primeiro tokenizado por um scanner manual, depois analisado por um parser preditivo LL(1) com tabela e pilha, convertido para uma AST, validado semanticamente e, por fim, traduzido para YAML compativel com o Home Assistant.

## 2. Definicao da linguagem

### 2.1 Objetivos de design

Os principais objetivos da linguagem Homi sao:

- fornecer uma sintaxe mais amigavel que YAML para automacoes residenciais;
- manter uma estrutura adequada para implementacao por scanner manual e parser LL(1);
- representar os padroes reais encontrados no arquivo de referencia do professor;
- separar claramente declaracoes, gatilhos, condicoes e acoes;
- facilitar futura extensao sem precisar criar uma palavra-chave para cada integracao do Home Assistant.

### 2.2 Sintaxe geral

A linguagem foi organizada em torno de declaracoes opcionais e blocos de automacao:

```text
entidade luz_sala = light.sala;
dispositivo cortina = cover device_id "abc" entity_id "cover.sala";

automacao "Sala - conforto" modo single {
    descricao "Liga a iluminacao no fim da tarde";

    gatilhos {
        quando sol por_do_sol offset "-00:45:00" id "sol";
    }

    condicoes {
        se estado luz_sala igual ["off"];
    }

    acoes {
        faca servico light.turn_on alvo {
            entity_id: [light.sala];
        } dados {
            brightness_pct: 80;
        };
    }
}
```

### 2.3 Exemplos simples

Um exemplo minimo com trigger de horario:

```text
automacao "Bom dia" modo single {
    gatilhos {
        quando hora "05:00:00" id "Hora";
    }

    acoes {
        espere 45s;
    }
}
```

Um exemplo com condicao e servico:

```text
automacao "Sala - noite" modo restart {
    gatilhos {
        quando estado [binary_sensor.movimento_sala] para ["on"] id "Movimento";
    }

    condicoes {
        se estado switch.luzes_da_sala igual ["off"];
    }

    acoes {
        faca servico light.turn_on alvo {
            entity_id: [light.sala];
        } dados {
            brightness_pct: 20;
        };
    }
}
```

A gramatica e os exemplos da linguagem foram projetados para cobrir os padroes observados em `examples/professor/automations_homi.yaml`, incluindo triggers `state`, `device`, `time` e `sun`, condicoes compostas e acoes por dispositivo e por servico.

## 3. Gramatica Livre de Contexto

### 3.1 Terminais

Os terminais da linguagem incluem:

- palavras reservadas, como `automacao`, `gatilhos`, `condicoes`, `acoes`, `quando`, `se`, `faca`, `espere`, `servico`, `modo`, `single`, `restart`;
- operadores e delimitadores, como `{`, `}`, `[`, `]`, `:`, `;`, `,` e `=`;
- tokens lexicos genericos, como `IDENTIFIER`, `DOTTED_ID`, `STRING`, `NUMBER`, `DURATION` e `EOF`.

Os detalhes completos estao em `docs/grammar.md` e na representacao interna em `src/grammar.py`.

### 3.2 Nao-terminais

Entre os nao-terminais principais estao:

- `program`
- `top_level_list`
- `automation_decl`
- `triggers_section`
- `conditions_section`
- `actions_section`
- `trigger_core`
- `condition_clause`
- `action_stmt`
- `service_action`

### 3.3 Principais producoes

Algumas producoes centrais da linguagem sao:

```text
program ::= top_level_list EOF

automation_decl ::= AUTOMACAO STRING MODO mode automation_block

automation_block ::= LBRACE
                     description_section_opt
                     triggers_section_opt
                     conditions_section_opt
                     actions_section_opt
                     RBRACE

trigger_stmt ::= QUANDO trigger_core SEMICOLON

condition_stmt ::= SE condition_clause condition_enabled_opt SEMICOLON

simple_action_stmt ::= FACA action_command action_enabled_opt SEMICOLON
                     | ESPERE duration_value action_enabled_opt SEMICOLON
```

### 3.4 Organizacao em secoes

A automacao foi organizada em tres secoes principais:

- `gatilhos`
- `condicoes`
- `acoes`

Essa escolha melhora a legibilidade da linguagem e tambem simplifica o processo de analise sintatica. Cada secao comeca com uma palavra-chave distinta, o que reduz ambiguidades.

### 3.5 Relacao com LL(1)

A organizacao em secoes, combinada com delimitadores explicitos e fatoracoes locais, ajuda a manter a gramatica adequada para analise LL(1). Em vez de depender de backtracking, o parser escolhe a producao correta com base apenas no nao-terminal atual e no token de lookahead.

Alguns ajustes estruturais foram necessarios, por exemplo:

- fatoracao de alternativas com prefixo comum em triggers solares;
- separacao entre valores atomicos, listas e mapas;
- uso de nao-terminais especificos para booleanos e duracoes.

## 4. Analise lexica

O scanner foi implementado manualmente em `src/scanner.py` como um DFA explicito. Em vez de usar ferramentas prontas como ANTLR, PLY ou Lark, o projeto define estados internos e transicoes controladas em codigo Python.

As principais classes de tokens reconhecidas sao:

- palavras-chave da linguagem;
- identificadores simples, como `luz_sala` e `timer_closet`;
- `DOTTED_ID`, usado para nomes como `light.sala`, `switch.turn_on` e `notify.mobile_app_zfold4`;
- strings entre aspas;
- numeros inteiros e decimais;
- duracoes compactas, como `45s`, `4min`, `1h` e `1min45s`;
- simbolos estruturais, como chaves, colchetes, `:` e `;`.

O scanner tambem reconhece comentarios de linha iniciados por `#`, ignora espacos em branco e preserva informacoes de linha e coluna para cada token.

O reconhecimento de alguns elementos funciona da seguinte forma:

- `STRING`: consome o texto entre aspas, com tratamento de escapes simples;
- `DOTTED_ID`: reconhece identificadores com pontos, usados tanto para entidades quanto para servicos;
- `DURATION`: interpreta sequencias numericas seguidas de unidades como `h`, `min` e `s`;
- `NUMBER`: aceita inteiros e decimais;
- comentarios: consomem todos os caracteres ate o fim da linha;
- simbolos: sao reconhecidos por tabela direta de caracteres.

As posicoes `linha` e `coluna` sao atualizadas a cada caractere consumido. Isso permite que erros lexicos sejam reportados com localizacao precisa sem interromper o programa.

## 5. Analise sintatica

O parser sintatico foi implementado em `src/parser_ll1.py` com base em uma tabela preditiva LL(1) gerada em `src/parser_table.py`. A logica central nao e de descida recursiva pura: a decisao de parsing vem da tabela, e a execucao usa pilha.

O algoritmo funciona, em linhas gerais, da seguinte maneira:

1. inicializa a pilha com `EOF` e `program`;
2. observa o topo da pilha e o token atual;
3. se o topo e terminal, compara com o token atual;
4. se o topo e nao-terminal, consulta a tabela LL(1);
5. empilha a producao escolhida em ordem reversa;
6. repete ate consumir a entrada.

Durante o processo, o parser monta uma arvore sintatica intermediaria, que depois e convertida para a AST da linguagem Homi.

### 5.1 Modo panico

Quando ocorre erro sintatico, o parser registra um `Diagnostic` e entra em modo panico. Nessa estrategia, tokens sao descartados ate um ponto de sincronizacao, permitindo continuar a analise e reportar mais de um erro em uma mesma entrada.

Os tokens de sincronizacao adotados foram:

- `SEMICOLON`
- `RBRACE`
- `RBRACKET`
- `EOF`

### 5.2 Exemplo de erro sintatico

O arquivo `examples/invalid_syntax/missing_semicolon.homi` omite `;` ao fim de uma declaracao. Nesse caso, o parser detecta a divergencia entre o terminal esperado e o token recebido, registra um diagnostico com linha e coluna e tenta prosseguir.

Outro exemplo didatico e `examples/invalid_syntax/wrong_section_order.homi`, em que `acoes` aparece antes de `gatilhos`. Como a gramatica fixa a ordem das secoes, o erro e sinalizado de forma previsivel.

## 6. Analise semantica

Depois da construcao da AST, a fase semantica verifica se o programa faz sentido dentro das regras do dominio. Essa etapa esta implementada principalmente em `src/semantic.py`, com apoio de `src/symbol_table.py`.

### 6.1 Tabela de simbolos

A tabela de simbolos armazena:

- entidades declaradas, com nome simbolico, `entity_id` e dominio;
- dispositivos declarados, com nome simbolico, dominio, `device_id` e `entity_id`.

### 6.2 Inferencia de dominio

Quando possivel, o dominio e inferido a partir do prefixo de um `entity_id`. Por exemplo:

- `light.sala` -> `light`
- `switch.luzes_da_sala` -> `switch`
- `media_player.sala` -> `media_player`

Essa inferencia e usada tanto para validar referencias diretas quanto para verificar compatibilidade entre servicos, acoes e tipos de entidade.

### 6.3 Regras de compatibilidade

Algumas regras implementadas sao:

- `ligar`, `desligar` e `alternar` so podem ser usados em dominios compativeis, como `light`, `switch` e `cover`;
- `abrir` e `fechar` sao restritos a `cover`;
- `timer.start` e `timer.finish` exigem `target` no dominio `timer`;
- `automation.trigger` exige `target` no dominio `automation`;
- servicos `media_player.*` exigem alvos do dominio `media_player` ou `device_id`;
- `notify.*` e `tts.speak` exigem dados textuais;
- `alexa_devices.send_text_command` exige `device_id` e `text_command`;
- `alexa_devices.send_sound` exige `device_id` e `sound`.

Tambem sao validadas:

- referencias simbolicas nao declaradas;
- ids de trigger inexistentes na mesma automacao;
- formato de horario;
- coerencia basica de triggers `state`, `device`, `time` e `sun`;
- modos de automacao (`single` e `restart`).

### 6.4 Exemplos de erro semantico

Os arquivos abaixo foram criados para demonstracao:

- `examples/invalid_semantic/turn_on_sensor.homi`: tenta ligar um sensor;
- `examples/invalid_semantic/unknown_trigger_id.homi`: usa um id de gatilho inexistente;
- `examples/invalid_semantic/wrong_cover_action.homi`: tenta abrir uma entidade que nao e `cover`;
- `examples/invalid_semantic/wrong_timer_target.homi`: usa `timer.start` com alvo invalido.

Pendente:

- a AST atual ainda nao preserva, para todos os nos, a origem completa de linha e coluna; por isso, a analise semantica usa posicao padrao em parte dos diagnosticos.

## 7. Geracao de YAML

A geracao de YAML foi implementada em `src/yaml_generator.py`. A entrada dessa fase e a AST ja validada semanticamente, e a saida e uma lista YAML de automacoes no formato esperado pelo Home Assistant.

O gerador realiza mapeamentos como:

- `Automation` -> item YAML com `alias`, `description`, `triggers`, `conditions`, `actions` e `mode`;
- `StateTrigger` -> `trigger: state`;
- `DeviceTrigger` -> `trigger: device` com normalizacao de tipos como `ligado -> turned_on`;
- `SunTrigger` -> `trigger: sun`;
- `TimeTrigger` -> `trigger: time`;
- `DeviceAction` -> `type: turn_on`, `turn_off`, `toggle`, `open` ou `close`;
- `ServiceAction` -> `action`, `target`, `data` e `metadata`;
- `DelayAction` -> bloco `delay`;
- `IfAction` -> estrutura `if/then/else`;
- `ChooseAction` -> estrutura `choose`.

### 7.1 Exemplo Homi -> YAML

Entrada Homi:

```text
automacao "Bom dia" modo single {
    gatilhos {
        quando hora "05:00:00" id "Hora";
    }

    acoes {
        espere 45s;
    }
}
```

Saida YAML:

```yaml
- alias: Bom dia
  description: ""
  triggers:
    - trigger: time
      at: "05:00:00"
      id: Hora
  conditions: []
  actions:
    - delay:
        hours: 0
        minutes: 0
        seconds: 45
        milliseconds: 0
  mode: single
```

Ao final da geracao, o YAML produzido e validado com `yaml.safe_load`. Isso garante que a serializacao produzida pelo compilador e sintaticamente carregavel pelo parser YAML da biblioteca.

## 8. Cobertura do YAML do professor

O projeto inclui uma etapa especifica de cobertura do arquivo `examples/professor/automations_homi.yaml`. Um script de analise em `tools/analyze_professor_yaml.py` inspeciona o YAML de referencia e gera um relatorio em `docs/professor_yaml_coverage.md`.

Esse levantamento mostrou que o material do professor utiliza, entre outros, os seguintes padroes:

- triggers `state`, `device`, `time` e `sun`;
- conditions `state`, `device`, `time`, `sun`, `trigger` e `or`;
- actions por servico, por dispositivo, `delay`, `if/then/else` e `choose`;
- campos especiais como `id`, `alias`, `from`, `to`, `above`, `below`, `for`, `enabled`, `brightness_pct`, `weekday`, `offset`, `target`, `data` e `metadata`.

Com base nisso, a linguagem Homi cobre:

- triggers `state/device/time/sun`;
- conditions `state/device/time/sun/trigger/or/and`;
- actions `service/device/delay/if/choose`.

Tambem foram produzidos exemplos equivalentes em Homi e os respectivos YAMLs gerados em:

- `examples/professor/homi_equivalents/`
- `examples/professor/generated_yaml/`

Para detalhes quantitativos e mapeamento padrao por padrao, ver `docs/professor_yaml_coverage.md`.

## 9. Testes e execucao

Os testes automatizados usam `pytest`. A forma mais direta de executa-los e:

```bash
make test
```

ou, alternativamente:

```bash
python -m pytest
```

Para compilar um exemplo Homi para YAML:

```bash
python -m src.main examples/valid/minimal.homi -o out/minimal.yaml
```

Para demonstrar erros:

```bash
python -m src.main examples/invalid_syntax/missing_semicolon.homi -o out/erro.yaml
python -m src.main examples/invalid_semantic/turn_on_sensor.homi -o out/erro.yaml
```

O projeto possui testes para:

- scanner;
- parser LL(1);
- AST;
- analise semantica;
- geracao de YAML;
- cobertura dos equivalentes do YAML do professor;
- exemplos didaticos de erro sintatico e semantico.

## 10. Conclusao

O projeto `homi-compiler` implementa as principais fases do front-end de um compilador aplicado a um problema concreto de automacao residencial. O trabalho inclui:

- analise lexica por DFA manual;
- analise sintatica por tabela preditiva LL(1) com pilha;
- construcao de AST;
- analise semantica com tabela de simbolos;
- inicio do back-end por geracao de YAML.

Tambem foi realizada uma etapa especifica de comparacao com o YAML de referencia do professor, o que ajudou a orientar a evolucao da linguagem Homi para cobrir padroes reais de uso do Home Assistant.

Pendente:

- preservar linha e coluna de forma mais fina em todos os nos da AST para melhorar os diagnosticos semanticos;
- expandir a linguagem para outros recursos futuros do Home Assistant alem dos padroes atualmente cobertos.
