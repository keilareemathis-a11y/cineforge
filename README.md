# CineForge

**AI filmmaking studio in the browser. Generate shots, manage versions, build timelines, and export films.**

---

## Overview

CineForge is an AI filmmaking tool that lets creators generate shots,
manage shot versions, build film drafts, and export finished films.

## Core Features

- AI shot generation
- Shot version history
- Timeline editor
- Regenerate shots without breaking the timeline
- Film export

## Architecture

CineForge is built around a versioned filmmaking data model:

```
Project
 └ FilmDraft        # a specific cut or version of the film
     └ TimelineItem  # an ordered slot in the film's timeline
         └ Shot      # a scene captured at a moment in time
             └ ShotVersion  # an individual AI-generated render of a shot
```

- **Project** – the top-level creative workspace for a film
- **FilmDraft** – a specific cut or assembly of the film's timeline
- **TimelineItem** – an ordered slot that holds a shot in the draft
- **Shot** – a single scene or moment; can have multiple versions
- **ShotVersion** – one AI-generated render of a shot; the active version is used in export

## Tech Stack

- **Frontend**: Next.js (TypeScript)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL + SQLAlchemy
- **Infrastructure**: Docker Compose

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
    app/api/    # Route handlers (films, shots, users, …)
```

## Getting Started

```bash
# Start everything with Docker
docker compose up -d

# Or run the frontend locally
cd apps/web
npm install
npm run dev   # http://localhost:3000
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/films?sort=trending` | Trending published films |
| `GET` | `/api/films/{id}` | Film detail + metadata |
| `GET` | `/api/films/{id}/timeline` | Timeline items with nested shots |
| `GET` | `/api/shots/{shotId}/versions` | All versions for a shot |
| `POST` | `/api/shots/{shotId}/regenerate` | Queue a new version |
| `GET` | `/api/users/@{handle}` | Creator profile + stats |

## License

[MIT](LICENSE)
