"""Centralized filesystem paths with env-var overrides and local fallbacks.

The app runs in Docker with mounted volumes at /data, /downloads and /logs.
On a plain host (e.g. `uv run python -m jncep_webui`) those paths do not
exist, so fall back to local directories in the current working directory.
"""

import os
from pathlib import Path


def _resolve_dir(env_var: str, docker_default: str) -> Path:
    """Resolve a directory used by the app.

    Precedence:
        1. Environment variable (e.g. JNCEP_DATA_DIR).
        2. The Docker default (e.g. /data) when it already exists.
        3. A local ./<name> directory, so the app also runs outside Docker.

    Args:
        env_var (str): Environment variable name to check for an override.
        docker_default (str): Path used inside the Docker container.

    Returns:
        Path: The resolved directory (created if missing).

    """
    configured = os.getenv(env_var)
    if configured:
        path = Path(configured)
    else:
        docker_path = Path(docker_default)
        path = docker_path if docker_path.exists() else Path(docker_path.name)

    # Make absolute: Flask's send_file() resolves relative paths against the
    # app root, which would break serving files from a relative fallback dir.
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = _resolve_dir("JNCEP_DATA_DIR", "/data")
DOWNLOADS_DIR = _resolve_dir("JNCEP_DOWNLOADS_DIR", "/downloads")
LOGS_DIR = _resolve_dir("JNCEP_LOGS_DIR", "/logs")

DB_PATH = DATA_DIR / "jncep_history.db"
