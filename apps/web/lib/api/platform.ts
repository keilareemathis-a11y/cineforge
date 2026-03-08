import type { PublishedFilm, CreatorProfile } from '../../types/platform';
import { mockFilms } from '../../mock/films';
import { mockCreators } from '../../mock/creators';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export async function getHomepageData(): Promise<{
  trending: PublishedFilm[];
  newReleases: PublishedFilm[];
  popularCreators: CreatorProfile[];
}> {
  try {
    const [trending, newReleases] = await Promise.all([
      apiFetch<PublishedFilm[]>('/api/films?sort=trending'),
      apiFetch<PublishedFilm[]>('/api/films?sort=new'),
    ]);
    const popularCreators = await apiFetch<CreatorProfile[]>('/api/users?sort=popular');
    return { trending, newReleases, popularCreators };
  } catch {
    const sorted = [...mockFilms].sort((a, b) => b.view_count - a.view_count);
    return {
      trending: sorted.slice(0, 3),
      newReleases: [...mockFilms].sort(
        (a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      ).slice(0, 3),
      popularCreators: mockCreators.slice(0, 3),
    };
  }
}

export async function getFilmById(id: string): Promise<PublishedFilm> {
  try {
    return await apiFetch<PublishedFilm>(`/api/films/${id}`);
  } catch {
    const film = mockFilms.find((f) => f.id === id);
    if (!film) throw new Error(`Film not found: ${id}`);
    return film;
  }
}

export async function getCreatorProfile(handle: string): Promise<CreatorProfile> {
  try {
    return await apiFetch<CreatorProfile>(`/api/users/@${handle}`);
  } catch {
    const creator = mockCreators.find((c) => c.handle === handle);
    if (!creator) throw new Error(`Creator not found: ${handle}`);
    return creator;
  }
}

export async function likeFilm(filmId: string): Promise<void> {
  if (!API_BASE) return;
  await fetch(`${API_BASE}/api/films/${filmId}/like`, { method: 'POST' });
}

export async function supportCreator(
  creatorId: string,
  amountCents: number
): Promise<{ clientSecret: string }> {
  const res = await fetch(`${API_BASE}/api/users/${creatorId}/support`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount_cents: amountCents }),
  });
  if (!res.ok) throw new Error('Support request failed');
  return res.json();
}
