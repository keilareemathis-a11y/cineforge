export interface PublishedFilm {
  id: string;
  title: string;
  description: string;
  thumbnail_url: string;
  video_url: string;
  duration_seconds: number;
  view_count: number;
  like_count: number;
  created_at: string;
  published_at: string;
  creator: CreatorProfile;
  tags: string[];
}

export interface CreatorProfile {
  id: string;
  handle: string;
  display_name: string;
  avatar_url: string;
  banner_url: string;
  bio: string;
  follower_count: number;
  total_views: number;
  film_count: number;
  films?: PublishedFilm[];
}

export interface FilmTimeline {
  film_id: string;
  timeline_items: TimelineItem[];
}

export interface TimelineItem {
  id: string;
  position: number;
  duration_seconds: number;
  shot: Shot;
}

export interface Shot {
  id: string;
  prompt: string;
  active_version_id: string;
  created_at: string;
}

export interface ShotVersion {
  id: string;
  shot_id: string;
  image_url: string;
  video_url?: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  created_at: string;
}

export interface ShotVersionsResponse {
  shot_id: string;
  active_version_id: string;
  versions: ShotVersion[];
}
