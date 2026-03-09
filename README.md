# CineForge

> AI filmmaking studio where creators generate shots, manage shot versions, build timelines, and export films.

---

## What It Is

CineForge is an AI filmmaking studio that lets creators generate shots,
manage shot versions, build film drafts with a timeline editor, and export
finished films — all from a single platform.

## Key Features

- AI shot generation
- Shot version history with non-destructive regeneration
- Timeline editor (drag shots into a draft, reorder, trim)
- Regenerate shots without breaking the timeline
- Film export

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
