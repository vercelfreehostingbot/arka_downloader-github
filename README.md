# Arka Downloader

**Arka Downloader 5.3.0 — Production Modular Edition**

A modular Telegram downloader built around aiogram 3, yt-dlp, gallery-dl and SQLite.
The original monolithic implementation has been decomposed into **68 ordered modules** while preserving the existing runtime flow and callback/handler names.

## Architecture

```text
.
├── bot.py                         # tiny production entrypoint
├── app/
│   ├── __init__.py
│   └── sections/                  # ordered domain modules
│       ├── s00_auto_version.py
│       ├── s01_paths.py
│       ├── s09_database.py
│       ├── s10_quality.py
│       ├── s11_models.py
│       ├── s12_repositories.py
│       ├── s18_downloader_core.py
│       ├── s23_job_pipeline.py
│       ├── s27_download.py
│       ├── s34_admin_helpers.py
│       ├── s35+_admin_*.py
│       └── s67_main.py
├── tests/
├── scripts/healthcheck.py
├── deploy/arkabot.service
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── .env.example
└── install.sh
```

The ordered section chain is intentional: it is a safe migration architecture that avoids introducing circular imports into a mature bot. Each section explicitly exports its runtime context, allowing further extraction into fully independent services without changing the public bot API in one large risky rewrite.

## Install

```bash
cp .env.example .env
nano .env
sudo bash install.sh install
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Development

```bash
make compile
make health
make test
make lint
```

## Production

### systemd

The installer can provision the service automatically. The template is also available at:

`deploy/arkabot.service`

### Docker

```bash
cp .env.example .env
# edit .env

docker compose up -d --build
```

## Required system software

- Python 3.10+
- FFmpeg
- Docker (when using the local Telegram Bot API mode)
- curl
- systemd (for service deployment)

## Security notes

- Never commit `.env` or bot tokens.
- Keep `data/cookies.txt` private and mode `600`.
- Run the service as a dedicated non-root user when possible.
- Keep `downloads/`, `logs/`, `backups/` and `updates/` writable only by the service account.
- Rotate backups and logs in production.

## Validation

The repository provides static validation even on machines where third-party Python packages are not installed:

```bash
python3 scripts/healthcheck.py
python3 -m compileall -q .
```

`tests/test_structure.py` verifies the modular layout, syntax and removal of the old monolithic file.

## Next refactor boundary

The current structure is the **safe production migration layer**. The next optional architectural iteration can move the ordered sections into independent packages (`core`, `database`, `downloader`, `bot/handlers`, `admin`, `ui`, `services`) one domain at a time. That migration should be done with integration tests enabled so no existing Telegram callback or FSM behavior is silently lost.

## Enterprise Hardening

This release adds an enterprise-ready foundation without forcing external infrastructure:

- **Observability:** Prometheus `/metrics`, `/health`, `/ready`, optional Sentry.
- **Scalability:** optional Redis client and a clear path to distributed state/queues.
- **Security:** external URL validation and environment-only secret configuration.
- **Database evolution:** Alembic/SQLAlchemy migration foundation; the existing SQLite migration runner remains the runtime source of truth until a deliberate PostgreSQL migration is performed.
- **Reliability:** graceful enterprise runtime shutdown, retry-ready dependencies, and deterministic health endpoints.
- **Operations:** reproducible CI, dependency/security audit hooks, database backup script, Docker/systemd deployment assets.

### Production environment

Copy `.env.example` to `.env` and set at minimum `BOT_TOKEN` and `OWNER_IDS`. Enable `REDIS_URL` and `SENTRY_DSN` only when those services are available.

### Checks

```bash
python -m compileall -q .
pytest
bash -n install.sh scripts/backup.sh
ruff check .
bandit -r app
pip-audit -r requirements.txt
```

The first three checks are expected to work in a minimal Python environment; the final checks require the development dependencies.


## Final hardening

The release includes optional Redis/ARQ queueing, PostgreSQL readiness checks, Prometheus metrics, Sentry integration, security headers, external-URL validation, CI quality gates, container health checks, non-root Docker execution, backup support, and migration scaffolding. Optional infrastructure is fail-safe: the base application can still start when those services are not configured.

### Validation performed

- Python compile/AST validation: passed
- Pytest suite: 7 passed
- Shell syntax: passed
- Enterprise smoke tests: passed
- Release asset checks: passed

A production deployment should still run the CI pipeline against the target Python version and perform live Telegram/PostgreSQL/Redis integration and load tests before public rollout.
