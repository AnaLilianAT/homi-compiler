from pathlib import Path

from src.main import compile_file
from src.parser_ll1 import LL1Parser
from src.scanner import Scanner
from src.semantic import SemanticAnalyzer


def test_invalid_syntax_examples_report_parser_diagnostics(tmp_path: Path) -> None:
    syntax_examples = [
        Path("examples/invalid_syntax/missing_semicolon.homi"),
        Path("examples/invalid_syntax/missing_closing_brace.homi"),
        Path("examples/invalid_syntax/wrong_section_order.homi"),
        Path("examples/invalid_syntax/invalid_action_syntax.homi"),
    ]

    for source_path in syntax_examples:
        scanner_result = Scanner(source_path.read_text(encoding="utf-8")).scan_tokens()
        parser = LL1Parser()
        _ = parser.parse(scanner_result.tokens)
        output_path = tmp_path / f"{source_path.stem}.yaml"

        assert scanner_result.diagnostics == [], source_path.name
        assert parser.diagnostics, source_path.name
        assert all(diagnostic.line >= 1 and diagnostic.column >= 1 for diagnostic in parser.diagnostics), source_path.name
        assert compile_file(source_path, output_path) == 1, source_path.name


def test_invalid_semantic_examples_report_semantic_diagnostics(tmp_path: Path) -> None:
    semantic_examples = [
        Path("examples/invalid_semantic/turn_on_sensor.homi"),
        Path("examples/invalid_semantic/unknown_trigger_id.homi"),
        Path("examples/invalid_semantic/wrong_cover_action.homi"),
        Path("examples/invalid_semantic/wrong_timer_target.homi"),
    ]

    for source_path in semantic_examples:
        scanner_result = Scanner(source_path.read_text(encoding="utf-8")).scan_tokens()
        parser = LL1Parser()
        program = parser.parse(scanner_result.tokens)
        diagnostics = SemanticAnalyzer().analyze(program)
        output_path = tmp_path / f"{source_path.stem}.yaml"

        assert scanner_result.diagnostics == [], source_path.name
        assert parser.diagnostics == [], source_path.name
        assert diagnostics, source_path.name
        assert all(diagnostic.line >= 1 and diagnostic.column >= 1 for diagnostic in diagnostics), source_path.name
        assert compile_file(source_path, output_path) == 1, source_path.name
