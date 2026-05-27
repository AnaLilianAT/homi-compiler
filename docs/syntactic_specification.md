# Especificacao Sintatica

O parser de Homi usa analise preditiva LL(1) com pilha. A decisao de qual producao aplicar vem da tabela em `src/parser_table.py`, e nao de descida recursiva como estrategia principal.

## Organizacao da gramatica

A linguagem foi organizada com secoes explicitas:

- `gatilhos { ... }`
- `condicoes { ... }`
- `acoes { ... }`

Essa escolha reduz ambiguidades porque cada secao comeca com uma palavra-chave distinta. Em uma automacao, o parser sabe exatamente em que parte esta apenas olhando o proximo token, o que favorece uma tabela LL(1) limpa.

Tambem foram aplicadas pequenas refatoracoes para manter a propriedade LL(1):

- fatoracao de prefixos em `sol ... offset ...`
- separacao de literais booleanos em um nao-terminal especifico
- separacao entre valores atomicos, listas e mapas pelos seus tokens iniciais
- uso de secoes e blocos com delimitadores explicitos

## Como a tabela LL(1) foi construida

A tabela preditiva e gerada a partir de:

1. conjunto `FIRST` de cada nao-terminal
2. conjunto `FOLLOW` de cada nao-terminal
3. preenchimento da tabela com a regra:
   - para cada producao `A -> alpha`, inserir a producao em `table[A][t]` para cada `t` em `FIRST(alpha)`
   - se `alpha` deriva `EPSILON`, inserir tambem para cada `t` em `FOLLOW(A)`

Se duas producoes diferentes disputarem a mesma celula, a construcao falha e a gramatica e considerada nao LL(1).

## Algoritmo do parser

O algoritmo central segue o formato canonico:

1. inicia a pilha com `EOF` e `Program`
2. se o topo da pilha e terminal, compara com o token atual
3. se o topo e nao-terminal, consulta `table[nao_terminal][lookahead]`
4. empilha a producao encontrada em ordem reversa
5. registra erro se nao houver producao valida

O parser tambem monta uma arvore sintatica intermediaria durante esse processo e depois a converte para a AST do projeto.

## Recuperacao em modo panico

Quando ocorre erro sintatico, o parser:

- registra um `Diagnostic`
- descarta tokens ate encontrar um token de sincronizacao
- tenta continuar a analise a partir desse ponto

Tokens de sincronizacao usados:

- `SEMICOLON`
- `RBRACE`
- `RBRACKET`
- `EOF`

Esses tokens foram escolhidos porque delimitam claramente fim de comando, fim de bloco ou fim de arquivo.

## Exemplos de erro sintatico

Os exemplos em `examples/invalid_syntax/` foram preparados para demonstracao em apresentacao:

- `missing_semicolon.homi`: falta `;` depois de uma declaracao
- `missing_closing_brace.homi`: falta `}` no fim da automacao
- `wrong_section_order.homi`: coloca `acoes` antes de `gatilhos`, violando a ordem fixa da gramatica
- `invalid_action_syntax.homi`: usa ordem invalida em uma acao, como `faca light ligar ...`

Mesmo quando encontra erro, o parser tenta continuar usando modo panico e sincronizacao por `;`, `}`, `]` e `EOF`.
