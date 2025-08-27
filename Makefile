    .PHONY: setup run test lint type sec clean

    setup:
	@echo "Install deps & prepare env"
	# python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

    run:
	@echo "Run the app (dev)"
	# uvicorn src.main:app --reload

    test:
	@echo "Run tests"
	# pytest --maxfail=1 --disable-warnings -q --cov=src --cov-report=xml:reports/coverage.xml

    lint:
	@echo "Run linters"
	# ruff src tests

    type:
	@echo "Run type checks"
	# mypy src

    sec:
	@echo "Run security checks"
	# pip-audit

    clean:
	@echo "Clean build artifacts"
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache reports/coverage.xml
