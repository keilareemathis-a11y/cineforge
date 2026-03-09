import type { FilmTimeline, ShotVersion, TimelineItem } from './platform';

export type EditorStatus = 'idle' | 'loading' | 'saving' | 'error';
export type VersionStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface EditorState {
  filmId: string;
  timeline: FilmTimeline | null;
  selectedTimelineItemId: string | null;
  selectedShotVersions: ShotVersion[];
  activeVersionId: string | null;
  renderedVideoUrl: string | null;
  publishedFilmId: string | null;
  status: EditorStatus;
  error: string | null;
}

export interface TimelineItemProps {
  item: TimelineItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onMoveUp: (id: string) => void;
  onMoveDown: (id: string) => void;
  onUpdateDuration: (id: string, duration: number) => void;
  isFirst: boolean;
  isLast: boolean;
}

export interface VersionPanelProps {
  shotId: string;
  activeVersionId: string | null;
  versions: ShotVersion[];
  onSelectVersion: (shotId: string, versionId: string) => void;
  onRegenerate: (shotId: string) => void;
  isLoading: boolean;
}
