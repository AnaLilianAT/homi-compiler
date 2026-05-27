# homi-compiler

Projeto-base de um compilador/tradutor para a linguagem Homi, com foco em gerar YAML compatível com o Home Assistant.

## Objetivo

O projeto foi organizado para cobrir as etapas clássicas de Compiladores:

- análise léxica com DFA manual
- análise sintática com tabela preditiva LL(1) e pilha
- análise semântica com tabela de símbolos
- geração de código YAML

## Estrutura

- `src/`: implementação principal do compilador
- `examples/`: exemplos de entrada e material de referência
- `tests/`: testes automatizados com `pytest`
- `docs/`: documentação da gramática e das especificações

## Requisitos

- Python 3.11+ recomendado

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
python -m src.main examples/valid/minimal.homi -o out/minimal.yaml
```

## Testes

```bash
python -m pytest
```

## Demonstracao de erros

Exemplos pequenos para apresentacao foram adicionados em:

- `examples/invalid_syntax/`
- `examples/invalid_semantic/`

Para demonstrar um erro sintatico:

```bash
python -m src.main examples/invalid_syntax/missing_semicolon.homi -o out/erro.yaml
```

Para demonstrar um erro semantico:

```bash
python -m src.main examples/invalid_semantic/turn_on_sensor.homi -o out/erro.yaml
```

O compilador imprime `Diagnostic` com mensagem e posicao `linha:coluna` quando essa informacao esta disponivel.

## Comandos de demonstracao

Para a apresentacao final, os comandos prontos sao:

```bash
make demo-valid
make demo-syntax-error
make demo-semantic-error
```

As flags de inspecao disponiveis no CLI sao:

- `--show-tokens`
- `--show-ast`
- `--show-symbols`
- `--validate-yaml`

## Estado atual

Esta entrega cria a base do projeto com:

- CLI funcional
- stubs dos módulos principais
- infraestrutura inicial de scanner, parser LL(1), semântica e geração de YAML
- testes mínimos de sanidade

O scanner e o parser ainda não implementam a linguagem Homi completa.
