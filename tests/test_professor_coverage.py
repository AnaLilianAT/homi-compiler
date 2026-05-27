from pathlib import Path

import yaml

from src.parser_ll1 import LL1Parser
from src.scanner import Scanner
from src.semantic import SemanticAnalyzer
from src.yaml_generator import generate_yaml


def test_professor_homi_equivalents_compile_and_match_generated_yaml() -> None:
    source_dir = Path("examples/professor/homi_equivalents")
    generated_dir = Path("examples/professor/generated_yaml")

    source_files = sorted(source_dir.glob("*.homi"))
    assert source_files

    for source_path in source_files:
        scanner_result = Scanner(source_path.read_text(encoding="utf-8")).scan_tokens()
        parser = LL1Parser()
        program = parser.parse(scanner_result.tokens)
        semantic_diagnostics = SemanticAnalyzer().analyze(program)
        yaml_text = generate_yaml(program)
        parsed_yaml = yaml.safe_load(yaml_text)

        assert scanner_result.diagnostics == [], source_path.name
        assert parser.diagnostics == [], source_path.name
        assert semantic_diagnostics == [], source_path.name
        assert isinstance(parsed_yaml, list), source_path.name
        assert parsed_yaml, source_path.name

        for automation in parsed_yaml:
            assert "alias" in automation, source_path.name
            assert "triggers" in automation, source_path.name
            assert "conditions" in automation, source_path.name
            assert "actions" in automation, source_path.name
            assert "mode" in automation, source_path.name

        expected_yaml_path = generated_dir / f"{source_path.stem}.yaml"
        assert expected_yaml_path.exists(), expected_yaml_path.as_posix()
        expected_yaml = yaml.safe_load(expected_yaml_path.read_text(encoding="utf-8"))
        assert parsed_yaml == expected_yaml, source_path.name
