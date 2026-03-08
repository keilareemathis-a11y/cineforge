import type { FilmTimeline, ShotVersion } from '../types/platform';

export const mockTimeline: FilmTimeline = {
  film_id: 'film-1',
  timeline_items: [
    {
      id: 'item-1',
      position: 0,
      duration_seconds: 5,
      shot: {
        id: 'shot-1',
        prompt: 'Wide establishing shot of a neon-lit city at night, rain-slicked streets reflecting colorful signs',
        active_version_id: 'version-1a',
        created_at: '2024-11-01T10:00:00Z',
      },
    },
    {
      id: 'item-2',
      position: 1,
      duration_seconds: 4,
      shot: {
        id: 'shot-2',
        prompt: 'Close-up of a hooded figure walking through a crowd, face partially obscured by rain',
        active_version_id: 'version-2a',
        created_at: '2024-11-01T10:05:00Z',
      },
    },
    {
      id: 'item-3',
      position: 2,
      duration_seconds: 6,
      shot: {
        id: 'shot-3',
        prompt: 'Aerial view of the city skyline transitioning from day to night, lights flickering on',
        active_version_id: 'version-3a',
        created_at: '2024-11-01T10:10:00Z',
      },
    },
    {
      id: 'item-4',
      position: 3,
      duration_seconds: 5,
      shot: {
        id: 'shot-4',
        prompt: 'Interior of a neon-lit bar, patrons with cybernetic enhancements talking quietly',
        active_version_id: 'version-4a',
        created_at: '2024-11-01T10:15:00Z',
      },
    },
  ],
};

export const mockVersions: Record<string, ShotVersion[]> = {
  'shot-1': [
    {
      id: 'version-1a',
      shot_id: 'shot-1',
      image_url: 'https://picsum.photos/seed/shot1a/640/360',
      status: 'ready',
      created_at: '2024-11-01T10:01:00Z',
    },
    {
      id: 'version-1b',
      shot_id: 'shot-1',
      image_url: 'https://picsum.photos/seed/shot1b/640/360',
      status: 'ready',
      created_at: '2024-11-01T10:30:00Z',
    },
  ],
  'shot-2': [
    {
      id: 'version-2a',
      shot_id: 'shot-2',
      image_url: 'https://picsum.photos/seed/shot2a/640/360',
      status: 'ready',
      created_at: '2024-11-01T10:06:00Z',
    },
  ],
  'shot-3': [
    {
      id: 'version-3a',
      shot_id: 'shot-3',
      image_url: 'https://picsum.photos/seed/shot3a/640/360',
      status: 'ready',
      created_at: '2024-11-01T10:11:00Z',
    },
    {
      id: 'version-3b',
      shot_id: 'shot-3',
      image_url: 'https://picsum.photos/seed/shot3b/640/360',
      status: 'ready',
      created_at: '2024-11-01T11:00:00Z',
    },
  ],
  'shot-4': [
    {
      id: 'version-4a',
      shot_id: 'shot-4',
      image_url: 'https://picsum.photos/seed/shot4a/640/360',
      status: 'ready',
      created_at: '2024-11-01T10:16:00Z',
    },
  ],
};
