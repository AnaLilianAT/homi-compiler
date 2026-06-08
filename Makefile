FILE ?= input.homi

run:
	python homi.py $(FILE)

test:
	python -m pytest tests/ -v

clean:
	rm -f parser.out parsetab.py
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true

install:
	pip install ply pyyaml pytest

.PHONY: run test clean install
