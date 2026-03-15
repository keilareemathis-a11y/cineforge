# CineForge

> An experimental **AI filmmaking studio** in the browser. Generate shots with
> OpenAI, manage versions, build timelines, and export films.

---

## Quick Start

```bash
# Clone and install dependencies
git clone https://github.com/keilareemathis-a11y/cineforge.git
cd cineforge

# Install root-level tooling
npm install

# Start the Next.js web app (studio + platform)
cd apps/web
cp .env.local.example .env.local   # add your OPENAI_API_KEY
npm install
npm run dev        # http://localhost:3000

# (Optional) Start the Python/FastAPI backend for platform pages
cd ../../apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
```

---

## Environment Variables

### `apps/web/.env.local`

Copy `apps/web/.env.local.example` → `apps/web/.env.local` and fill in:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Optional* | OpenAI API key for DALL-E 3 shot generation. Get one at [platform.openai.com](https://platform.openai.com/api-keys). If omitted, a placeholder image is used instead. |
| `NEXT_PUBLIC_API_URL` | Optional | URL of the FastAPI backend for platform (homepage/films/creators) pages. Defaults to `http://localhost:8000`. |

> **CI / GitHub Actions**: add `OPENAI_API_KEY` as a
> [repository secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
> named `OPENAI_API_KEY`. The Next.js build does **not** embed it (it is
> server-side only).

> **Security**: `OPENAI_API_KEY` is consumed only in Next.js API routes (server
> side). It is never sent to the browser and is not prefixed with `NEXT_PUBLIC_`.

---

## Dev Commands

```bash
# Web app (apps/web/)
npm run dev       # Start dev server  -> http://localhost:3000
npm run build     # Production build
npm run start     # Start production server
npm run lint      # ESLint

# Python API (apps/api/)
uvicorn app.main:app --reload   # Start API server -> http://localhost:8000
python -m pytest -q             # Run API tests

# Docker (everything at once)
docker compose up -d
```

---

## App Structure

```
apps/
├── web/                     # Next.js 14 app (React, TypeScript)
│   ├── app/
│   │   ├── page.tsx         # Platform home (trending films, creators)
│   │   ├── projects/        # Studio: project list, detail, timeline
│   │   ├── film/[filmId]/   # Film viewer
│   │   ├── films/[filmId]/editor/  # Film editor (legacy)
│   │   ├── creator/[handle]/       # Creator profile
│   │   └── api/             # Next.js API routes (self-contained MVP backend)
│   │       ├── projects/    # Projects CRUD
│   │       ├── shots/       # Shots CRUD + OpenAI generation
│   │       ├── timeline/    # Timeline CRUD + clip reorder
│   │       └── export/      # Export stub
│   ├── components/
│   │   ├── studio/          # Studio UI: ProjectCard, ShotCard, CreateShotForm
│   │   ├── editor/          # Film editor (EditorClient)
│   │   └── platform/        # Platform UI: FilmCard, CreatorCard, ...
│   ├── lib/
│   │   ├── store.ts         # JSON file persistence layer (see below)
│   │   └── api/             # API clients for platform pages (with mock fallback)
│   ├── types/               # Shared TypeScript contracts
│   ├── mock/                # Sample data for offline platform pages
│   └── data/                # Git-ignored runtime data (db.json created on first run)
└── api/                     # Python / FastAPI backend
    ├── app/
    │   ├── api/routes/      # projects, shots, scenes, drafts, films, users, ...
    │   ├── models/          # SQLAlchemy ORM models
    │   ├── core/            # DB init, config, queue
    │   └── services/        # render, generated visuals, platform
    └── tests/               # pytest suite
```

---

## How It Works

### Studio flow (Next.js-only, no Python backend required)

```
/projects               -> List / create projects
/projects/[id]          -> Create shots with a text prompt
                           Click "Generate" -> calls POST /api/shots/[id]/generate
                             -> OpenAI DALL-E 3 generates a film-still image
                             -> Result stored as a new ShotVersion
                           Click "+ Timeline" -> adds the shot as a clip
/projects/[id]/timeline -> Drag-to-reorder clips
                           Click "Export Film" -> calls POST /api/export/[id]
                             -> Returns a manifest (stub; no actual rendering yet)
```

### Data Model (Next.js / JSON store)

```
Project
  └─ Shot (has a text prompt + active version)
      └─ ShotVersion (image_url from DALL-E 3, provider, version_number)
Timeline (per project)
  └─ Clip (shot_id, version_id, position, duration)
```

Data is persisted to `apps/web/data/db.json` (auto-created, gitignored).

### Platform flow (FastAPI backend required)

```
/               -> Trending films, new releases, popular creators
/film/[id]      -> Film detail + viewer
/creator/[handle] -> Creator profile
```

---

## Persistence

The studio (projects / shots / timeline) uses a **flat JSON file** stored at
`apps/web/data/db.json`. This is intentional for MVP simplicity and local
development. For production, replace `apps/web/lib/store.ts` with a proper
database adapter (e.g., Prisma + SQLite/Postgres).

---

## API Routes (Next.js)

| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/api/projects` | List all projects |
| `POST`   | `/api/projects` | Create a project |
| `GET`    | `/api/projects/[id]` | Get project by ID |
| `PATCH`  | `/api/projects/[id]` | Update project |
| `DELETE` | `/api/projects/[id]` | Delete project (cascades) |
| `GET`    | `/api/shots?project_id=` | List shots (optionally filter) |
| `POST`   | `/api/shots` | Create a shot |
| `GET`    | `/api/shots/[id]` | Get shot |
| `PATCH`  | `/api/shots/[id]` | Update shot |
| `DELETE` | `/api/shots/[id]` | Delete shot |
| `GET`    | `/api/shots/[id]/versions` | List versions (newest first) |
| `POST`   | `/api/shots/[id]/versions/[vId]/select` | Set active version |
| `POST`   | `/api/shots/[id]/generate` | Generate image via OpenAI DALL-E 3 |
| `GET`    | `/api/timeline/[projectId]` | Get (or create) project timeline |
| `POST`   | `/api/timeline/[projectId]/clips` | Add clip to timeline |
| `DELETE` | `/api/timeline/[projectId]/clips/[clipId]` | Remove clip |
| `POST`   | `/api/timeline/[projectId]/reorder` | Reorder clips (`{ clip_ids: [...] }`) |
| `POST`   | `/api/export/[projectId]` | Export stub — returns manifest JSON |

---

## FastAPI Backend API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/projects` | Create a project |
| `GET`  | `/api/projects/{project_id}` | Get project by ID |
| `POST` | `/api/shots` | Create a shot |
| `GET`  | `/api/shots/{shot_id}` | Get shot by ID |
| `GET`  | `/api/shots/{shot_id}/versions` | List versions |
| `POST` | `/api/shots/{shot_id}/regenerate` | Generate new version |
| `POST` | `/api/drafts/{draft_id}/timeline-items` | Add shot to timeline |
| `GET`  | `/api/drafts/{draft_id}/timeline` | Retrieve full editorial timeline |

---

## Running Tests

```bash
# Next.js API smoke tests
cd apps/web
npm test

# Python API tests
cd apps/api
python -m pytest -q
```

---

## License

[MIT](LICENSE)
