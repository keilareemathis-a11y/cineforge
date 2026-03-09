# CineForge

>CineForge is an experimental AI filmmaking backend that generates shots, versions them, lets you edit them in a timeline, and renders a finished film.

The system models a non-linear editing workflow similar to professional editors, but with AI-generated footage.

---

Architecture

The platform follows this pipeline:

Project
   ↓
Scene
   ↓
Shot
   ↓
ShotVersion
   ↓
TimelineItem
   ↓
FilmDraft
   ↓
Rendered Film

This allows:

shot regeneration

non-destructive editing

timeline-based film assembly

MP4 rendering
## Data Model

```
Project
  └─ FilmDraft
      └─ TimelineItem
          └─ Shot
              └─ ShotVersion
```

## Project Structure

```
apps/
  web/          # Next.js frontend
    app/        # Pages (homepage, film, creator, editor)
    components/ # Platform & editor UI components
    lib/api/    # API clients with mock fallback
    types/      # Shared TypeScript contracts
    mock/       # Local sample data
  api/          # FastAPI backend
    app/
      api/      # Route handlers
        routes/ # projects, shots, drafts, films, scenes, …
      models/   # SQLAlchemy ORM models
      core/     # database, config, queue
      services/ # business logic (timeline assembly, …)
    tests/      # pytest test suite
```

## Getting Started

```bash
# Start everything with Docker
docker compose up -d

# Or run the frontend locally
cd apps/web
npm install
npm run dev   # http://localhost:3000

# Run the API locally
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/projects` | Create a project |
| `GET`  | `/api/projects/{project_id}` | Get project by ID |
| `POST` | `/api/shots` | Create a shot |
| `GET`  | `/api/shots/{shot_id}` | Get shot by ID |
| `GET`  | `/api/shots/{shot_id}/versions` | List versions (newest first) |
| `POST` | `/api/shots/{shot_id}/regenerate` | Generate new version, propagate to timeline |
| `POST` | `/api/drafts/{draft_id}/timeline-items` | Add shot to timeline |
| `GET`  | `/api/drafts/{draft_id}/timeline` | Retrieve full editorial timeline |

## Running Tests

```bash
cd apps/api
pip install -r requirements.txt
pytest tests/
```

## License

[MIT](LICENSE)
