from pathlib import Path

from src.main import compile_file


def test_demo_valid_file_compiles_with_debug_flags(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "demo_valid.yaml"

    exit_code = compile_file(
        Path("demo/02_valido_professor_complexo.homi"),
        output_path,
        show_tokens=True,
        show_ast=True,
        show_symbols=True,
        validate_yaml=True,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "TOKENS:" in captured.out
    assert "AST:" in captured.out
    assert "SYMBOLS:" in captured.out
    assert "- alias: Demo complexo" in captured.out
    assert "YAML validado com sucesso." in captured.err


def test_demo_syntax_error_returns_failure(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "demo_syntax_error.yaml"

    exit_code = compile_file(
        Path("demo/03_erro_sintatico.homi"),
        output_path,
        show_tokens=True,
        show_ast=True,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "TOKENS:" in captured.out
    assert "AST:" in captured.out
    assert "Expected" in captured.err or "Unexpected token" in captured.err


def test_demo_semantic_error_returns_failure(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "demo_semantic_error.yaml"

    exit_code = compile_file(
        Path("demo/04_erro_semantico.homi"),
        output_path,
        show_tokens=True,
        show_ast=True,
        show_symbols=True,
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "TOKENS:" in captured.out
    assert "AST:" in captured.out
    assert "SYMBOLS:" in captured.out
    assert "not compatible with domain 'sensor'" in captured.err
