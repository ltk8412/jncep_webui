# JNCEP WebUI — Suggested Commands

## Dev

```bash
uv sync --locked                          # Install dependencies
uv run src/jncep_webui/app.py             # Run dev server (port 5000)
uv run ruff check .                       # Lint
uv run basedpyright                       # Type-check
```

## Docker

```bash
docker compose up                         # Start with compose
docker compose down                       # Stop
docker build -t jncep_webui .            # Build image
```

## Git

```bash
git log --oneline -10                     # Recent commits
git diff                                  # Unstaged changes
```

## Environment

```bash
export JNCEP_EMAIL=user@example.com
export JNCEP_PASSWORD=secret
```

## Testing

No test suite yet (TODO: https://github.com/NaruZosa/jncep_webui/issues/2).
Manual test: `curl "http://localhost:5000/epub?jnovelclub_url=https://j-novel.club/series/..."` with env vars set.
