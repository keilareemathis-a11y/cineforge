import type { FilmTimeline, ShotVersionsResponse } from '../../types/platform';
import { mockTimeline, mockVersions } from '../../mock/timeline';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

interface BackendTimelineItem {
  timeline_item_id: string;
  position: number;
  duration_seconds?: number | null;
  trim_start?: number | null;
  trim_end?: number | null;
  shot?: {
    shot_id: string;
    prompt?: string;
    image_prompt?: string;
    active_version_id?: string;
    created_at?: string;
    storyboard_image?: string;
  } | null;
  active_version?: {
    version_id: string;
    version_number?: number;
    duration_seconds?: number;
    trim_start?: number | null;
    trim_end?: number | null;
    image_url?: string;
    video_url?: string;
    provider?: string;
    status?: 'pending' | 'processing' | 'ready' | 'failed';
    created_at?: string;
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
  version_number?: number;
  duration_seconds?: number;
  trim_start?: number | null;
  trim_end?: number | null;
  image_url?: string;
  video_url?: string;
  provider?: string;
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
        duration_seconds: item.duration_seconds ?? item.active_version?.duration_seconds ?? 1,
        trim_start: item.trim_start ?? 0,
        trim_end: item.trim_end ?? null,
        shot: {
          id: item.shot?.shot_id ?? item.timeline_item_id,
          prompt: item.shot?.prompt ?? item.shot?.image_prompt ?? 'Generated shot',
          active_version_id: item.shot?.active_version_id ?? item.active_version?.version_id ?? '',
          created_at: item.shot?.created_at ?? new Date().toISOString(),
          storyboard_image: item.shot?.storyboard_image ?? item.active_version?.image_url ?? '',
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
      versions: versions.map(mapVersion),
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
      versions: response.versions.map(mapVersion),
    };
  } catch {
    const versions = mockVersions[shotId] ?? [];
    return { shot_id: shotId, active_version_id: versionId, versions };
  }
}

export async function regenerateShot(
  shotId: string,
  provider: 'runway' | 'pika' | 'stable-video-diffusion'
): Promise<ShotVersionsResponse> {
  try {
    await apiFetch(`/api/shots/${shotId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider }),
    });
    return loadVersions(shotId);
  } catch {
    const existing = mockVersions[shotId] ?? [];
    const newVersion = {
      id: `version-${shotId}-${Date.now()}`,
      shot_id: shotId,
      image_url: `https://picsum.photos/seed/${Date.now()}/640/360`,
      video_url: '',
      provider,
      status: 'ready' as const,
      created_at: new Date().toISOString(),
    };
    const updated = [newVersion, ...existing];
    mockVersions[shotId] = updated;
    return {
      shot_id: shotId,
      active_version_id: newVersion.id,
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

export async function publishFilm(
  filmId: string,
  tags: string[]
): Promise<{ id: string }> {
  const response = await apiFetch<{ id: string }>(`/api/films/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ draft_id: filmId, tags }),
  });
  return response;
}

export async function reorderTimelineItem(
  filmId: string,
  itemId: string,
  newPosition: number
): Promise<FilmTimeline> {
  try {
    const response = await apiFetch<BackendTimelineResponse>(`/api/films/${filmId}/timeline/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId, new_position: newPosition }),
    });
    return {
      film_id: response.film_draft_id,
      timeline_items: response.timeline_items.map((item) => ({
        id: item.timeline_item_id,
        position: item.position,
        duration_seconds: item.duration_seconds ?? item.active_version?.duration_seconds ?? 1,
        trim_start: item.trim_start ?? 0,
        trim_end: item.trim_end ?? null,
        shot: {
          id: item.shot?.shot_id ?? item.timeline_item_id,
          prompt: item.shot?.prompt ?? item.shot?.image_prompt ?? 'Generated shot',
          active_version_id: item.shot?.active_version_id ?? item.active_version?.version_id ?? '',
          created_at: item.shot?.created_at ?? new Date().toISOString(),
          storyboard_image: item.shot?.storyboard_image ?? item.active_version?.image_url ?? '',
        },
      })),
    };
  } catch {
    const tl = { ...mockTimeline, film_id: filmId };
    const items = [...tl.timeline_items];
    const currentIndex = items.findIndex((item) => item.id === itemId);
    const [removed] = items.splice(currentIndex, 1);
    items.splice(newPosition, 0, removed);
    return { ...tl, timeline_items: items.map((item, index) => ({ ...item, position: index })) };
  }
}

export async function moveTimelineItem(
  filmId: string,
  itemId: string,
  direction: 'up' | 'down'
): Promise<FilmTimeline> {
  try {
    const response = await apiFetch<BackendTimelineResponse>(`/api/films/${filmId}/timeline/${itemId}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction }),
    });
    return {
      film_id: response.film_draft_id,
      timeline_items: response.timeline_items.map((item) => ({
        id: item.timeline_item_id,
        position: item.position,
        duration_seconds: item.duration_seconds ?? item.active_version?.duration_seconds ?? 1,
        trim_start: item.trim_start ?? 0,
        trim_end: item.trim_end ?? null,
        shot: {
          id: item.shot?.shot_id ?? item.timeline_item_id,
          prompt: item.shot?.prompt ?? item.shot?.image_prompt ?? 'Generated shot',
          active_version_id: item.shot?.active_version_id ?? item.active_version?.version_id ?? '',
          created_at: item.shot?.created_at ?? new Date().toISOString(),
          storyboard_image: item.shot?.storyboard_image ?? item.active_version?.image_url ?? '',
        },
      })),
    };
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

export async function updateTimelineItem(
  filmId: string,
  itemId: string,
  payload: { duration_seconds?: number; trim_start?: number; trim_end?: number | null }
): Promise<FilmTimeline> {
  const response = await apiFetch<BackendTimelineResponse>(`/api/films/${filmId}/timeline/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return {
    film_id: response.film_draft_id,
    timeline_items: response.timeline_items.map((item) => ({
      id: item.timeline_item_id,
      position: item.position,
      duration_seconds: item.duration_seconds ?? item.active_version?.duration_seconds ?? 1,
      trim_start: item.trim_start ?? 0,
      trim_end: item.trim_end ?? null,
      shot: {
        id: item.shot?.shot_id ?? item.timeline_item_id,
        prompt: item.shot?.prompt ?? item.shot?.image_prompt ?? 'Generated shot',
        active_version_id: item.shot?.active_version_id ?? item.active_version?.version_id ?? '',
        created_at: item.shot?.created_at ?? new Date().toISOString(),
        storyboard_image: item.shot?.storyboard_image ?? item.active_version?.image_url ?? '',
      },
    })),
  };
}

function mapVersion(version: BackendShotVersion) {
  return {
    id: version.id,
    shot_id: version.shot_id,
    version_number: version.version_number,
    duration_seconds: version.duration_seconds,
    trim_start: version.trim_start ?? 0,
    trim_end: version.trim_end ?? null,
    image_url: version.image_url ?? '',
    video_url: version.video_url ? `${API_BASE}${version.video_url}` : '',
    provider: version.provider ?? 'runway',
    status: version.status ?? 'ready',
    created_at: version.created_at,
  };
}
