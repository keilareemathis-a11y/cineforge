import type { FilmTimeline, ShotVersionsResponse } from '../../types/platform';
import { mockTimeline, mockVersions } from '../../mock/timeline';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

interface BackendTimelineItem {
  timeline_item_id: string;
  position: number;
  shot?: {
    shot_id: string;
    prompt?: string;
    image_prompt?: string;
    active_version_id?: string;
    created_at?: string;
  } | null;
  active_version?: {
    version_id: string;
    duration_seconds?: number;
  } | null;
}

interface BackendTimelineResponse {
  film_draft_id: string;
  timeline_items: BackendTimelineItem[];
}

interface BackendShotResponse {
  id: string;
  active_version_id?: string | null;
  prompt?: string;
  created_at?: string;
}

interface BackendShotVersion {
  id: string;
  shot_id: string;
  image_url?: string;
  status?: 'pending' | 'processing' | 'ready' | 'failed';
  created_at: string;
}

interface BackendSelectVersionResponse {
  shot_id: string;
  active_version_id: string;
  versions: BackendShotVersion[];
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export async function loadTimeline(filmId: string): Promise<FilmTimeline> {
  try {
    const response = await apiFetch<BackendTimelineResponse>(`/api/films/${filmId}/timeline`);
    return {
      film_id: response.film_draft_id,
      timeline_items: response.timeline_items.map((item) => ({
        id: item.timeline_item_id,
        position: item.position,
        duration_seconds: item.active_version?.duration_seconds ?? 1,
        shot: {
          id: item.shot?.shot_id ?? item.timeline_item_id,
          prompt: item.shot?.prompt ?? item.shot?.image_prompt ?? 'Generated shot',
          active_version_id: item.shot?.active_version_id ?? item.active_version?.version_id ?? '',
          created_at: item.shot?.created_at ?? new Date().toISOString(),
        },
      })),
    };
  } catch {
    return { ...mockTimeline, film_id: filmId };
  }
}

export async function loadVersions(shotId: string): Promise<ShotVersionsResponse> {
  try {
    const [versions, shot] = await Promise.all([
      apiFetch<BackendShotVersion[]>(`/api/shots/${shotId}/versions`),
      apiFetch<BackendShotResponse>(`/api/shots/${shotId}`),
    ]);

    return {
      shot_id: shotId,
      active_version_id: shot.active_version_id ?? versions[0]?.id ?? '',
      versions: versions.map((version) => ({
        id: version.id,
        shot_id: version.shot_id,
        image_url: version.image_url ?? '',
        status: version.status ?? 'ready',
        created_at: version.created_at,
      })),
    };
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
    const response = await apiFetch<BackendSelectVersionResponse>(
      `/api/shots/${shotId}/versions/${versionId}/select`,
      { method: 'POST' }
    );
    return {
      shot_id: response.shot_id,
      active_version_id: response.active_version_id,
      versions: response.versions.map((version) => ({
        id: version.id,
        shot_id: version.shot_id,
        image_url: version.image_url ?? '',
        status: version.status ?? 'ready',
        created_at: version.created_at,
      })),
    };
  } catch {
    const versions = mockVersions[shotId] ?? [];
    return { shot_id: shotId, active_version_id: versionId, versions };
  }
}

export async function regenerateShot(shotId: string): Promise<ShotVersionsResponse> {
  try {
    await apiFetch(`/api/shots/${shotId}/regenerate`, {
      method: 'POST',
    });
    return loadVersions(shotId);
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

export async function renderFilm(filmId: string): Promise<{ videoUrl: string }> {
  const response = await apiFetch<{ video_url: string }>(`/api/films/${filmId}/render`, {
    method: 'POST',
  });
  return {
    videoUrl: `${API_BASE}${response.video_url}`,
  };
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
