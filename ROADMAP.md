# CineForge Roadmap

> AI filmmaking studio where creators generate shots, manage shot versions, build timelines, and export films.

---

## Current State (v0.1)

- SQLAlchemy ORM models: `Project`, `FilmDraft`, `Shot`, `ShotVersion`, `TimelineItem`
- FastAPI backend with full shot versioning and timeline management
- Non-destructive regeneration: new `ShotVersion` is created and propagated to all timeline items automatically
- pytest test suite covering all core endpoints

## Milestones

### ✅ Phase 1 — Core Backend (complete)

- [x] Data model: `Project → FilmDraft → TimelineItem → Shot → ShotVersion`
- [x] Shot CRUD endpoints
- [x] Shot versioning: `GET /api/shots/{shot_id}/versions` (ordered newest-first)
- [x] Regenerate: `POST /api/shots/{shot_id}/regenerate` with timeline propagation
- [x] Timeline management: `POST/GET /api/drafts/{draft_id}/timeline-items`
- [x] Project creation and retrieval
- [x] Comprehensive pytest test suite

### 🔜 Phase 2 — AI Generation

- [ ] AI shot generation (image/video from prompt)
- [ ] Script → storyboard → scenes pipeline
- [ ] Async job queue for generation tasks

### 🔜 Phase 3 — Editor & Export

- [ ] Web-based timeline editor (drag, reorder, trim)
- [ ] Film export (concatenate shots into final video)
- [ ] Preview playback

### 🔜 Phase 4 — Platform

- [ ] Creator accounts and authentication
- [ ] Public film publishing and discovery
- [ ] Creator profiles and stats

### 🔜 Phase 5 — Scale

- [ ] CDN for video/image delivery
- [ ] Usage analytics and monitoring
- [ ] Community features (comments, likes)

---

## Success Metrics

- Shot regeneration latency (target < 30 s)
- Timeline round-trip API latency (target < 100 ms)
- Test coverage (target > 90%)
- Creator adoption rate

---

*Last updated: 2026-03-09*
