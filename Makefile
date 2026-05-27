PYTHON ?= python
INPUT ?= examples/valid/minimal.homi
OUTPUT ?= out/output.yaml

.PHONY: run test clean demo-valid demo-syntax-error demo-semantic-error

run:
	$(PYTHON) -m src.main $(INPUT) -o $(OUTPUT)

test:
	$(PYTHON) -m pytest

demo-valid:
	$(PYTHON) -m src.main demo/02_valido_professor_complexo.homi -o out/demo_valid.yaml --show-tokens --show-ast --show-symbols --validate-yaml

demo-syntax-error:
	$(PYTHON) -m src.main demo/03_erro_sintatico.homi -o out/demo_syntax_error.yaml --show-tokens --show-ast

demo-semantic-error:
	$(PYTHON) -m src.main demo/04_erro_semantico.homi -o out/demo_semantic_error.yaml --show-tokens --show-ast --show-symbols

clean:
	powershell -NoProfile -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force .pytest_cache, out -ErrorAction SilentlyContinue"
