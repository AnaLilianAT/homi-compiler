# Roteiro de Apresentacao

## 1. Problema

- YAML do Home Assistant e poderoso, mas verboso e pouco amigavel para usuarios leigos.
- Automacoes maiores ficam dificeis de escrever e manter manualmente.

## 2. Linguagem Homi

- Homi abstrai os detalhes do YAML.
- A linguagem usa blocos claros de `gatilhos`, `condicoes` e `acoes`.

## 3. Scanner

- Mostrar que o scanner e manual e baseado em DFA.
- Destacar tokens como `IDENTIFIER`, `DOTTED_ID`, `STRING`, `DURATION` e palavras-chave.

## 4. Parser LL(1)

- Explicar pilha, tabela preditiva e lookahead.
- Ressaltar que nao e descida recursiva simples.

## 5. Semantico

- Mostrar tabela de simbolos.
- Explicar validacoes de dominio, trigger id e compatibilidade de acoes.

## 6. Geracao YAML

- Mostrar a traducao da AST para YAML do Home Assistant.
- Destacar validacao com `yaml.safe_load`.

## 7. Demonstracao de erro

- Rodar `make demo-syntax-error`.
- Mostrar diagnosticos sintaticos com linha e coluna e comentar o modo panico.
- Rodar `make demo-semantic-error`.
- Mostrar erro de compatibilidade semantica.

## 8. Demonstracao de exemplo valido

- Rodar `make demo-valid`.
- Mostrar tokens, AST, tabela de simbolos e YAML gerado.
