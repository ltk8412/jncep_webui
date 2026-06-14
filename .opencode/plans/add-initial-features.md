# Implementation Plan: Download History & Destination Selection

## Summary

Add a download history table (SQLAlchemy + SQLite) to track every EPUB generation. Display the history on the homepage with per-row delete buttons that remove both the DB entry and the server-side file. Add download destination checkboxes (default: save to server `/downloads/` on, download to client off). Bump jncep from v53 to v55.

## Database & File Layout (hardcoded paths — Docker)

| Path | Purpose |
|------|---------|
| `/data/jncep_history.db` | SQLite database file |
| `/downloads/` | EPUB/ZIP files saved to server |

Both paths hardcoded. `/data/` and `/downloads/` are separate Docker volumes.

## Database Changes

**New dependency:** `sqlalchemy` (>=2.0) added to `pyproject.toml`.

**New model — `src/jncep_webui/models.py`:**

```python
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class DownloadHistory(Base):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]              # novel title extracted from output filename
    jnovelclub_url: Mapped[str]
    prepub_parts: Mapped[str]
    output_filenames: Mapped[str]   # comma-separated EPUB/ZIP filenames
    saved_to_server: Mapped[bool]   # whether saved to /downloads/
    downloaded_to_client: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**DB initialization — `src/jncep_webui/database.py`:**

```python
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DB_PATH = Path("/data/jncep_history.db")

engine = create_engine(f"sqlite:///{DB_PATH}")

def init_db() -> None:
    from .models import Base
    Base.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
```

DB is created on first app startup inside `main()` (call `init_db()` before `serve()`). No migration tool — `create_all` on startup is sufficient for a single-table SQLite DB.

## Backend Route Changes

### Modified: `GET|POST /epub` — download generation

**Current behavior:** generates EPUB → always sends file to browser.

**New behavior:** accepts two additional form fields / query params:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `save_to_server` | bool (`"on"`/absent) | **on** | Save EPUB to `/downloads/` on server |
| `download_to_client` | bool (`"on"`/absent) | **off** | Return file to browser |

**Skeleton flow in `download_epub()`:**

```python
@app.route("/epub", methods=["GET", "POST"])
def download_epub() -> Response:
    # ... existing credential + form parsing ...

    # Parse destination flags
    save_to_server = request.args.get("save_to_server", "on") == "on"
    download_to_client = request.args.get("download_to_client") == "on"

    with tempfile.TemporaryDirectory() as output_dir:
        output_path = Path(output_dir)
        generate_epub_files(jnc_user, jnc_form_data, output_path)
        file_obj, filename, mimetype = prepare_epub_download(output_path)

        # Extract title from filename: "Series_Name_Volume_4.epub" → "Series_Name"
        title = Path(filename).stem.split("_Volume_")[0]

        # Record history
        with get_session() as session:
            session.add(DownloadHistory(
                title=title,
                jnovelclub_url=jnc_form_data.jnovelclub_url,
                prepub_parts=jnc_form_data.prepub_parts,
                output_filenames=filename,
                saved_to_server=save_to_server,
                downloaded_to_client=download_to_client,
            ))
            session.commit()

        # Save to server if requested
        if save_to_server:
            server_dir = Path("/downloads")
            server_dir.mkdir(parents=True, exist_ok=True)
            _ = (server_dir / filename).write_bytes(file_obj.getvalue())
            file_obj.seek(0)

        # Send to client if requested
        if download_to_client:
            return send_file(file_obj, download_name=filename,
                             mimetype=mimetype, as_attachment=True)

    # Server-save only → redirect to homepage to show updated history
    return redirect("/")
```

### New: `POST /epub/delete/<int:id>` — delete entry + file

```python
@app.route("/epub/delete/<int:id>", methods=["POST"])
def delete_download(id: int) -> Response:
    with get_session() as session:
        entry = session.get(DownloadHistory, id)
        if entry is None:
            raise TerminateRequestError("Download entry not found", 404)

        # Delete server-side file if it was saved
        if entry.saved_to_server:
            file_path = Path("/downloads") / entry.output_filenames
            if file_path.exists():
                file_path.unlink()

        session.delete(entry)
        session.commit()

    return redirect("/")
```

### Modified: `GET /` — homepage now shows history table

```python
@app.route("/")
def homepage() -> str:
    with get_session() as session:
        history = session.query(DownloadHistory) \
            .order_by(DownloadHistory.created_at.desc()) \
            .all()

    return render_template("Homepage.html", history=history)
```

## Frontend Changes

### Modified: `templates/Homepage.html`

Add checkbox group (defaults flipped: save-to-server ON, download-to-client OFF) and history table below the form:

```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Prepub Downloader</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
        <link rel="favicon" href="{{ url_for('static', filename='favicon.ico') }}">
    </head>

    <body>
        <div class="container">
            <div>
                <form id="PrepubForm" action="/epub" method="GET">
                    <h3>J-Novel Club Prepub Downloader</h3>
                    <h4>Paste the URL of the series and specify what parts to download</h4>
                    <fieldset>
                        <label for="JNC_URL">J-Novel Club URL:</label>
                        <input id="JNC_URL" placeholder="https://j-novel.club/series/her-majesty-s-swarm"
                               name="jnovelclub_url" type="text" tabindex="1" required autofocus>
                        <label for="JNC_PARTS">Prepub parts:</label>
                        <input id="JNC_PARTS" placeholder="4.1:4.2" name="prepub_parts"
                               type="text" tabindex="1" autofocus>
                    </fieldset>
                    <fieldset class="destination-group">
                        <legend>Download destination:</legend>
                        <label>
                            <input type="checkbox" name="save_to_server" checked>
                            Save to server (/downloads)
                        </label>
                        <label>
                            <input type="checkbox" name="download_to_client">
                            Download to my computer
                        </label>
                    </fieldset>
                    <fieldset>
                        <div style="text-align:center;">
                            <button name="submit" type="submit" id="FormSubmit"
                                    data-submit="...Sending">Submit</button>
                        </div>
                    </fieldset>
                    <footer id="footer">
                        Parts: Specify a range of parts to download in the form of
                        [vol].[part] or [vol].[part]:[vol].[part]
                        <br>
                        Default: All the content linked by the URL. This will be a single part,
                        a volume or the whole series
                        <br><br>
                        Specifications for how parts can be defined are listed
                        <a href="https://github.com/gvellut/jncep#range-of-parts">here</a>
                    </footer>
                </form>
            </div>

            {% if history %}
            <div id="history-section">
                <h3>Download History</h3>
                <table id="history-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Series URL</th>
                            <th>Parts</th>
                            <th>Output</th>
                            <th>Server</th>
                            <th>Client</th>
                            <th>Date</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for entry in history %}
                        <tr>
                            <td class="title-cell">{{ entry.title }}</td>
                            <td class="url-cell">{{ entry.jnovelclub_url }}</td>
                            <td>{{ entry.prepub_parts or "—" }}</td>
                            <td>{{ entry.output_filenames }}</td>
                            <td>{{ "✓" if entry.saved_to_server else "—" }}</td>
                            <td>{{ "✓" if entry.downloaded_to_client else "—" }}</td>
                            <td>{{ entry.created_at.strftime("%Y-%m-%d %H:%M") }}</td>
                            <td>
                                <form action="/epub/delete/{{ entry.id }}" method="POST"
                                      style="display:inline;">
                                    <button type="submit" class="delete-btn"
                                            onclick="return confirm('Delete this entry and its file?')">
                                        Delete
                                    </button>
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
    </body>
</html>
```

### Modified: `static/css/main.css`

Add styles for checkboxes, history table, and delete button:

```css
#PrepubForm input[type="checkbox"] {
    width: auto;
    margin-right: 6px;
}

.destination-group legend {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
}

.destination-group label {
    display: block;
    margin: 4px 0;
    font-size: 14px;
}

#history-section {
    background: #F9F9F9;
    padding: 25px;
    margin: 0 0 150px 0;
    box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.24);
}

#history-section h3 {
    font-size: 20px;
    margin-bottom: 15px;
}

#history-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}

#history-table th, #history-table td {
    padding: 6px 8px;
    border-bottom: 1px solid #ddd;
    text-align: left;
}

#history-table th {
    background: #f0f0f0;
    font-weight: 600;
}

#history-table .url-cell {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

#history-table .title-cell {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.delete-btn {
    cursor: pointer;
    border: none;
    background: #e74c3c;
    color: #FFF;
    padding: 4px 10px;
    font-size: 12px;
    border-radius: 4px;
}

.delete-btn:hover {
    background: #c0392b;
}
```

## Infrastructure Changes

### Docker / compose.yml

Separate volumes for DB and downloads:

```yaml
---
services:
  jncep-webui:
    image: ghcr.io/naruzosa/jncep_webui:latest
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - JNCEP_EMAIL=${JNCEP_EMAIL}
      - JNCEP_PASSWORD=${JNCEP_PASSWORD}
      - PYTHONUNBUFFERED=1
    ports:
      - "5000:5000"
    volumes:
      - ./logs:/logs
      - ./data:/data            # SQLite DB
      - ./downloads:/downloads  # EPUB files
    restart: unless-stopped
```

### Dependencies (`pyproject.toml`)

```toml
dependencies = [
    "flask==3.1.1",
    "waitress==3.0.2",
    "jncep==55",               # bumped from 53 → 55
    "loguru==0.7.3",
    "sqlalchemy>=2.0.0",       # NEW
]
```

## Key Service Objects/Classes

| File | Class/Function | Role |
|------|---------------|------|
| `src/jncep_webui/models.py` | `DownloadHistory` | ORM model for download records |
| `src/jncep_webui/database.py` | `engine`, `init_db()`, `get_session()` | DB lifecycle |
| `src/jncep_webui/app.py` | `download_epub()` (modified) | Route: destination logic + history recording |
| `src/jncep_webui/app.py` | `homepage()` (modified) | Route: query history, pass to template |
| `src/jncep_webui/app.py` | `delete_download()` (new) | Route: delete DB entry + server file |

## Testing Focus

- `GET /` → shows homepage with empty history (no table section)
- `GET /epub?jnovelclub_url=...` with no checkboxes → save to server only (defaults), redirect to `/`
- `GET /epub?jnovelclub_url=...&save_to_server=on&download_to_client=on` → file saved to `/downloads/` + file download
- `GET /` after downloads → table shows entries with correct flags and title
- `POST /epub/delete/1` → entry removed from DB, file deleted from `/downloads/`
- `POST /epub/delete/999` (nonexistent) → returns 404
- Verify `/downloads/filename.epub` exists when `save_to_server=on`
- Verify file is deleted after row is deleted
- `uv run ruff check .` and `uv run basedpyright` pass

## Dependencies/Blockers

None. All changes additive.

## Deployment Notes

- `jncep==55` — must regenerate `uv.lock` (`uv lock` / `uv sync --locked` won't work until lockfile updated).
- Docker: `./data/` and `./downloads/` directories created by Docker if they don't exist locally.
- `/data/` and `/downloads/` must be writable inside the container.
- Existing API consumers can still trigger downloads via query params, but defaults have changed (save-to-server now on, download-to-client off).

