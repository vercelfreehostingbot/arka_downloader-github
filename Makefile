.PHONY: install test lint security typecheck audit verify migrate backup
install:
	python -m pip install -r requirements.txt -r requirements-dev.txt
test:
	pytest --cov=app --cov=infra --cov-report=term-missing
lint:
	ruff check .
security:
	bandit -q -r app infra
typecheck:
	mypy app infra --ignore-missing-imports
audit:
	pip-audit -r requirements.txt
migrate:
	alembic upgrade head
backup:
	bash scripts/backup.sh
verify: test lint security typecheck audit
