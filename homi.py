#!/usr/bin/env python3
"""
homi — Compilador da linguagem Homi para YAML do Home Assistant

Uso:
    python homi.py <arquivo.homi>
    python homi.py <arquivo.homi> -o <saida.yaml>
    python homi.py <arquivo.homi> --check      # só verifica erros
    python homi.py <arquivo.homi> --ast        # imprime AST

Fases executadas em sequência:
    1. Análise Léxica    (lexer.py   — PLY lex, DFA)
    2. Análise Sintática (parser.py  — PLY yacc, LALR(1))
    3. Análise Semântica (semantic.py — tabela de símbolos + checagem de tipos)
    4. Geração de Código (codegen.py  — AST → YAML Home Assistant)
"""

import sys
import os
import argparse


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog='homi',
        description='Compilador Homi → YAML Home Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Exemplos:\n'
            '  python homi.py automacao.homi\n'
            '  python homi.py automacao.homi -o resultado.yaml\n'
            '  python homi.py automacao.homi --check\n'
        ),
    )
    ap.add_argument('arquivo', help='Arquivo fonte .homi')
    ap.add_argument(
        '-o', '--output',
        metavar='SAIDA',
        help='Arquivo .yaml de saída (padrão: mesmo nome do .homi)',
    )
    ap.add_argument(
        '--check', action='store_true',
        help='Apenas verifica erros; não gera arquivo de saída',
    )
    ap.add_argument(
        '--ast', action='store_true',
        help='Imprime a AST no stdout em vez de gerar YAML',
    )
    return ap


# ---------------------------------------------------------------------------
# Pipeline de compilação
# ---------------------------------------------------------------------------

def compilar(source: str, nome_arquivo: str):
    """
    Executa as 4 fases do compilador sobre o código-fonte.
    Retorna (ast, yaml_str) ou termina com sys.exit(1) em caso de erro.
    """

    # ------------------------------------------------------------------
    # Fase 1 — Análise Léxica
    # ------------------------------------------------------------------
    from lexer import build_lexer
    lexer = build_lexer()

    # ------------------------------------------------------------------
    # Fase 2 — Análise Sintática
    # ------------------------------------------------------------------
    from parser import build_parser, get_parse_errors
    parser = build_parser()

    print(f"[1/4] Análise léxica e sintática de '{nome_arquivo}'...")
    ast = parser.parse(source, lexer=lexer)

    erros_lex  = lexer.lex_errors
    erros_sint = get_parse_errors()

    if erros_lex or erros_sint:
        total = len(erros_lex) + len(erros_sint)
        _sep()
        print(f"Compilação interrompida: {total} erro(s) léxico(s)/sintático(s).")
        sys.exit(1)

    print(f"      OK — {len(ast.automations)} automação(ões) reconhecida(s).")

    # ------------------------------------------------------------------
    # Fase 3 — Análise Semântica
    # ------------------------------------------------------------------
    from semantic import SemanticAnalyzer
    print("[2/4] Análise semântica...")
    sem = SemanticAnalyzer()
    sem_ok = sem.analyze(ast)

    if sem.warnings:
        for w in sem.warnings:
            print(f"      Aviso: {w}")

    if not sem_ok:
        _sep()
        print(f"Compilação interrompida: {len(sem.errors)} erro(s) semântico(s).")
        sys.exit(1)

    print(f"      OK — sem erros semânticos.")

    # ------------------------------------------------------------------
    # Fase 4 — Geração de Código (YAML)
    # ------------------------------------------------------------------
    from codegen import YAMLGenerator
    print("[3/4] Geração de código YAML...")
    yaml_str = YAMLGenerator().generate(ast)
    print(f"      OK — {yaml_str.count('alias:')} bloco(s) gerado(s).")

    return ast, yaml_str


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap   = _build_argparser()
    args = ap.parse_args()

    # Lê arquivo fonte
    try:
        with open(args.arquivo, encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: '{args.arquivo}'", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Erro ao ler '{args.arquivo}': {e}", file=sys.stderr)
        sys.exit(1)

    nome = os.path.basename(args.arquivo)
    _sep()
    print(f"  Homi Compiler — {nome}")
    _sep()

    ast, yaml_str = compilar(source, nome)

    # ------------------------------------------------------------------
    # Saída
    # ------------------------------------------------------------------
    if args.ast:
        print("\n[AST]")
        _print_ast(ast)
        sys.exit(0)

    if args.check:
        _sep()
        print("Verificação concluída: nenhum erro encontrado.")
        sys.exit(0)

    # Determina caminho do arquivo de saída
    if args.output:
        out_path = args.output
    else:
        base     = os.path.splitext(args.arquivo)[0]
        out_path = base + '.yaml'

    print(f"[4/4] Escrevendo '{out_path}'...")
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(yaml_str)
    except OSError as e:
        print(f"Erro ao escrever '{out_path}': {e}", file=sys.stderr)
        sys.exit(1)

    _sep()
    print(f"  Sucesso: {len(ast.automations)} automacao(es) compilada(s) -> '{out_path}'")
    _sep()


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _sep():
    print("-" * 54)


def _print_ast(ast):
    """Impressão legível da AST para fins de depuração."""
    from ast_nodes import ActionNode, ChoiceNode

    for auto in ast.automations:
        print(f'\nAutomação: "{auto.name}"  [modo={auto.mode}]')
        print(f'  Gatilhos ({len(auto.triggers)}):')
        for t in auto.triggers:
            print(f'    {t}')
        print(f'  Condições ({len(auto.conditions)}):')
        for c in auto.conditions:
            print(f'    {c}')
        print(f'  Ações ({len(auto.actions)}):')
        _print_actions(auto.actions, indent=4)


def _print_actions(actions, indent: int):
    from ast_nodes import ActionNode, ChoiceNode
    pad = ' ' * indent
    for a in actions:
        if a.kind == 'if':
            print(f'{pad}if {a.conditions}')
            print(f'{pad}  então:')
            _print_actions(a.then_actions, indent + 4)
            if a.else_actions:
                print(f'{pad}  senão:')
                _print_actions(a.else_actions, indent + 4)
        elif a.kind == 'escolher':
            print(f'{pad}escolher:')
            for ch in a.choices:
                print(f'{pad}  caso {ch.conditions}:')
                _print_actions(ch.actions, indent + 4)
        else:
            print(f'{pad}{a}')


if __name__ == '__main__':
    main()
