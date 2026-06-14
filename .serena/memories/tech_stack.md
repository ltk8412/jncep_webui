# JNCEP WebUI — Tech Stack

- **Language:** Python 3.13+
- **Web framework:** Flask 3.1.1
- **WSGI server:** waitress 3.0.2
- **EPUB generation:** jncep 53 (CLI wrapper)
- **HTTP client:** httpx (via jncep.jncapi)
- **Logging:** loguru 0.7.3
- **Package manager:** uv (uv.lock, pyproject.toml)
- **Build backend:** uv-build
- **Linter:** ruff (ALL rules, ignore E501/D203/D213/D202/DOC502/CPY001)
- **Type checker:** basedpyright (dev), basedmypy (dev)
- **Containerization:** Docker (multi-stage, python:3.13-alpine, uv 0.7.21)
- **CI:** GitHub Actions (.github/)
- **Frontend:** Server-rendered Jinja2 HTML, no JS framework
- **Database:** None currently. SQLite + SQLAlchemy planned.

## Dev commands

```bash
uv sync --locked          # install deps
uv run ruff check .       # lint
uv run basedpyright       # type-check
uv run src/jncep_webui/app.py  # run
```
