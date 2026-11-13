# JNCEP WebUI — Task Completion Checklist

After any code change, run:

```bash
uv run ruff check .       # Must pass (0 errors)
uv run basedpyright       # Must pass (0 errors)
```

If runtime behavior changed:
- Test `GET /epub?jnovelclub_url=...` with valid credentials
- Test `GET /health` returns 200
- Test `GET /` returns homepage HTML

Docker changes additionally:
- `docker compose build` must succeed
- `docker compose up` must serve on port 5000
