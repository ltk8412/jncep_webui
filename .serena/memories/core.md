# JNCEP WebUI — Core

Flask-based web app wrapping `jncep` CLI to generate EPUBs from J-Novel Club pre-pub parts.

## Layout

```
src/jncep_webui/
  app.py          — Flask routes + core logic + WSGI entrypoint
  __main__.py     — `python -m jncep_webui` entry
  __init__.py     — re-exports app, setup_logging
  logger_setup.py — Loguru config, intercepts stdlib logging
  templates/      — Jinja2 templates (single Homepage.html)
  static/css/     — main.css
```

## Entrypoints

- Native: `python -m jncep_webui` or `python src/jncep_webui/app.py`
- Docker: `CMD ["python", "-m", "jncep_webui"]` → port 5000
- `uv run src/jncep_webui/app.py`

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Homepage form |
| GET/POST | `/epub` | Generate EPUB from `jnovelclub_url` + `prepub_parts` query params, return file |
| GET | `/health` | Healthcheck JSON |

## Key invariants

- Logs go to `/logs/jncep.log` (rotates at 50MB, 1-week retention)
- EPUB generation uses `jncep.cli.epub.generate_epub.callback()` with temp dir
- Multi-volume output → single ZIP; single volume → direct EPUB
- No database currently; fully stateless
- `mem:tech_stack` for stack details
- `mem:conventions` for code style
