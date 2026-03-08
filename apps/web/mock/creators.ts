import type { CreatorProfile } from '../types/platform';
import { mockFilms } from './films';

export const mockCreators: CreatorProfile[] = [
  {
    id: 'user-1',
    handle: 'nova_frames',
    display_name: 'Nova Frames',
    avatar_url: 'https://picsum.photos/seed/creator1/80/80',
    banner_url: 'https://picsum.photos/seed/banner1/1200/300',
    bio: 'Visual storyteller crafting AI-powered short films. Based in Los Angeles.',
    follower_count: 3200,
    total_views: 89000,
    film_count: 14,
    films: mockFilms.filter((f) => f.creator.id === 'user-1'),
  },
  {
    id: 'user-2',
    handle: 'echo_director',
    display_name: 'Echo Director',
    avatar_url: 'https://picsum.photos/seed/creator2/80/80',
    banner_url: 'https://picsum.photos/seed/banner2/1200/300',
    bio: 'Telling human stories through AI-generated visuals. Focused on intimate character studies.',
    follower_count: 1800,
    total_views: 42000,
    film_count: 7,
    films: mockFilms.filter((f) => f.creator.id === 'user-2'),
  },
  {
    id: 'user-3',
    handle: 'cosmic_cuts',
    display_name: 'Cosmic Cuts',
    avatar_url: 'https://picsum.photos/seed/creator3/80/80',
    banner_url: 'https://picsum.photos/seed/banner3/1200/300',
    bio: 'Space epics in 5 minutes or less. Sci-fi enthusiast and AI film pioneer.',
    follower_count: 5600,
    total_views: 134000,
    film_count: 22,
    films: mockFilms.filter((f) => f.creator.id === 'user-3'),
  },
];
