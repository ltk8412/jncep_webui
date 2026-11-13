# JNCEP WebUI — Conventions

## Code style

- `ruff` with `select = ["ALL"]`, ignores E501/D203/D213/D202/DOC502/CPY001
- Google-style docstrings with Args/Returns/Raises sections
- Type-annotated everywhere; use `@override`, `@final` from Python stdlib
- `from __future__ import annotations` NOT used; types are runtime resolvable
- Exception handling: custom `TerminateRequestError` raised for Flask error responses
- Dataclasses for data models (`JNCUser`, `JNovelFormData`)
- No `as any`, `@ts-ignore`, or type suppression

## Naming

- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_leading_underscore`

## Patterns

- Flask routes return `Response` or `str` (via `render_template`)
- EPUB flow: parse params → get credentials → `tempfile.TemporaryDirectory()` → `generate_epub_files()` → `prepare_epub_download()` → `send_file()`
- Credentials: query params override env vars; both or neither must be present (XOR validation)
- Signal handling: `SIGTERM` → graceful exit (required for Docker)
