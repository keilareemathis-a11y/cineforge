import type { FilmTimeline, ShotVersionsResponse } from '../../types/platform';
import { mockTimeline, mockVersions } from '../../mock/timeline';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export async function loadTimeline(filmId: string): Promise<FilmTimeline> {
  try {
    return await apiFetch<FilmTimeline>(`/api/films/${filmId}/timeline`);
  } catch {
    return { ...mockTimeline, film_id: filmId };
  }
}

export async function loadVersions(shotId: string): Promise<ShotVersionsResponse> {
  try {
    return await apiFetch<ShotVersionsResponse>(`/api/shots/${shotId}/versions`);
  } catch {
    const versions = mockVersions[shotId] ?? [];
    return {
      shot_id: shotId,
      active_version_id: versions[0]?.id ?? '',
      versions,
    };
  }
}

export async function selectVersion(
  shotId: string,
  versionId: string
): Promise<ShotVersionsResponse> {
  try {
    return await apiFetch<ShotVersionsResponse>(`/api/shots/${shotId}/versions/${versionId}/select`, {
      method: 'POST',
    });
  } catch {
    const versions = mockVersions[shotId] ?? [];
    return { shot_id: shotId, active_version_id: versionId, versions };
  }
}

export async function regenerateShot(shotId: string): Promise<ShotVersionsResponse> {
  try {
    return await apiFetch<ShotVersionsResponse>(`/api/shots/${shotId}/regenerate`, {
      method: 'POST',
    });
  } catch {
    const existing = mockVersions[shotId] ?? [];
    const newVersion = {
      id: `version-${shotId}-${Date.now()}`,
      shot_id: shotId,
      image_url: `https://picsum.photos/seed/${Date.now()}/640/360`,
      status: 'pending' as const,
      created_at: new Date().toISOString(),
    };
    const updated = [newVersion, ...existing];
    mockVersions[shotId] = updated;
    return {
      shot_id: shotId,
      active_version_id: existing[0]?.id ?? newVersion.id,
      versions: updated,
    };
  }
}

export async function moveTimelineItem(
  filmId: string,
  itemId: string,
  direction: 'up' | 'down'
): Promise<FilmTimeline> {
  try {
    return await apiFetch<FilmTimeline>(`/api/films/${filmId}/timeline/${itemId}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction }),
    });
  } catch {
    const tl = { ...mockTimeline, film_id: filmId };
    const items = [...tl.timeline_items].sort((a, b) => a.position - b.position);
    const idx = items.findIndex((i) => i.id === itemId);
    if (direction === 'up' && idx > 0) {
      [items[idx - 1], items[idx]] = [items[idx], items[idx - 1]];
    } else if (direction === 'down' && idx < items.length - 1) {
      [items[idx], items[idx + 1]] = [items[idx + 1], items[idx]];
    }
    return { ...tl, timeline_items: items.map((it, i) => ({ ...it, position: i })) };
  }
}

export async function updateDuration(
  filmId: string,
  itemId: string,
  durationSeconds: number
): Promise<void> {
  if (!API_BASE) return;
  await fetch(`${API_BASE}/api/films/${filmId}/timeline/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ duration_seconds: durationSeconds }),
  });
}
