# CineForge

**AI short-film creation and publishing platform.**

Go from prompt or script → storyboard → AI-generated scenes → published short film, in minutes.

---

## What It Is

CineForge is an open platform where independent creators use AI to write, visualize, and publish short films. Anyone can watch films on the homepage, follow creators, and support them directly.

## Key Features

- **Create** – Write a prompt or script; CineForge generates a storyboard and shot-by-shot visuals
- **Edit** – Rearrange timeline items, swap shot versions, adjust durations, regenerate any shot
- **Publish** – One click to publish; the film appears on your creator profile and the homepage
- **Discover** – Browse trending films, new releases, and popular creators
- **Support** – Tip creators directly ($1 / $3 / $5) via Stripe

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, React 18 |
| Backend | Python, FastAPI |
| Database | PostgreSQL (via SQLAlchemy / Alembic) |
| Infrastructure | Docker Compose |

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
