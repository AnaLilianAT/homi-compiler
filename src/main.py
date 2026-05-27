from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from pprint import pformat
import sys

import yaml

from .parser_ll1 import LL1Parser
from .scanner import Scanner, ScannerResult
from .semantic import SemanticAnalyzer
from .yaml_generator import generate_yaml


@dataclass
class CompilationResult:
    scanner_result: ScannerResult
    parser: LL1Parser
    program: object
    semantic_analyzer: SemanticAnalyzer
    semantic_diagnostics: list
    yaml_text: str | None

    @property
    def diagnostics(self) -> list:
        return (
            self.scanner_result.diagnostics
            + self.parser.diagnostics
            + self.semantic_diagnostics
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="homi-compiler",
        description="Compilador base da linguagem Homi para YAML do Home Assistant.",
    )
    parser.add_argument("source", help="Arquivo fonte .homi")
    parser.add_argument("-o", "--output", required=True, help="Arquivo YAML de saida")
    parser.add_argument("--show-tokens", action="store_true", help="Exibe os tokens produzidos pelo scanner.")
    parser.add_argument("--show-ast", action="store_true", help="Exibe a AST produzida pelo parser.")
    parser.add_argument(
        "--show-symbols",
        action="store_true",
        help="Exibe a tabela de simbolos apos a analise semantica.",
    )
    parser.add_argument(
        "--validate-yaml",
        action="store_true",
        help="Valida explicitamente o YAML gerado com yaml.safe_load.",
    )
    return parser


def compile_source(source: str) -> CompilationResult:
    scanner_result = Scanner(source).scan_tokens()
    parser = LL1Parser()
    program = parser.parse(scanner_result.tokens)
    semantic_analyzer = SemanticAnalyzer()
    semantic_diagnostics = semantic_analyzer.analyze(program)

    yaml_text: str | None = None
    if not (scanner_result.diagnostics or parser.diagnostics or semantic_diagnostics):
        yaml_text = generate_yaml(program)

    return CompilationResult(
        scanner_result=scanner_result,
        parser=parser,
        program=program,
        semantic_analyzer=semantic_analyzer,
        semantic_diagnostics=semantic_diagnostics,
        yaml_text=yaml_text,
    )


def compile_file(
    source_path: Path,
    output_path: Path,
    *,
    show_tokens: bool = False,
    show_ast: bool = False,
    show_symbols: bool = False,
    validate_yaml: bool = False,
) -> int:
    source = source_path.read_text(encoding="utf-8")
    result = compile_source(source)

    if show_tokens:
        _print_tokens(result.scanner_result)

    if show_ast:
        _print_ast(result.program)

    if show_symbols:
        _print_symbols(result.semantic_analyzer)

    if result.diagnostics:
        for diagnostic in result.diagnostics:
            print(diagnostic, file=sys.stderr)
        return 1

    assert result.yaml_text is not None

    if validate_yaml:
        yaml.safe_load(result.yaml_text)
        print("YAML validado com sucesso.", file=sys.stderr)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.yaml_text, encoding="utf-8")
    print(result.yaml_text, end="")
    return 0


def _print_tokens(scanner_result: ScannerResult) -> None:
    print("TOKENS:")
    for token in scanner_result.tokens:
        print(
            f"  {token.token_type.name:<15} lexeme={token.lexeme!r} "
            f"line={token.line} column={token.column}"
        )


def _print_ast(program: object) -> None:
    print("AST:")
    print(pformat(asdict(program), sort_dicts=False))


def _print_symbols(semantic_analyzer: SemanticAnalyzer) -> None:
    print("SYMBOLS:")
    print(pformat(semantic_analyzer.symbol_table.to_debug_dict(), sort_dicts=False))


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    return compile_file(
        Path(args.source),
        Path(args.output),
        show_tokens=args.show_tokens,
        show_ast=args.show_ast,
        show_symbols=args.show_symbols,
        validate_yaml=args.validate_yaml,
    )


if __name__ == "__main__":
    raise SystemExit(main())
