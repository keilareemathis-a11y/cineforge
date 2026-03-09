# CineForge

**AI short-film creation and publishing platform.**

Go from prompt or script → storyboard → AI-generated scenes → published short film, in minutes.

---

## What It Is

CineForge is an AI filmmaking tool that lets creators generate shots, 
manage shot versions, build film drafts, and export finished films.

## Key Features

- • AI shot generation
• Shot version history
• Timeline editor
• Regenerate shots without breaking the timeline
• Film export
## Tech Stack
Project
 └ FilmDraft
     └ TimelineItem
         └ Shot
             └ ShotVersion

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
