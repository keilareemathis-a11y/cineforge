'use client';
import { useState, useEffect, useCallback } from 'react';
import type { ShotVersionsResponse } from '../../types/platform';
import type { EditorState } from '../../types/editor';
import {
  loadTimeline,
  loadVersions,
  selectVersion,
  regenerateShot,
  renderFilm,
  publishFilm,
  reorderTimelineItem,
  moveTimelineItem,
  updateTimelineItem,
} from '../../lib/api/editor';
import Link from 'next/link';

interface EditorClientProps {
  filmId: string;
}

const PROVIDERS = [
  { value: 'runway', label: 'Runway' },
  { value: 'pika', label: 'Pika' },
  { value: 'stable-video-diffusion', label: 'Stable Video Diffusion' },
] as const;

export default function EditorClient({ filmId }: EditorClientProps) {
  const [state, setState] = useState<EditorState>({
    filmId,
    timeline: null,
    selectedTimelineItemId: null,
    selectedShotVersions: [],
    activeVersionId: null,
    renderedVideoUrl: null,
    publishedFilmId: null,
    status: 'loading',
    error: null,
  });
  const [generationProvider, setGenerationProvider] =
    useState<(typeof PROVIDERS)[number]['value']>('runway');
  const [publishTags, setPublishTags] = useState('ai,short-film');
  const [draggedItemId, setDraggedItemId] = useState<string | null>(null);

  const [, setVersionsData] = useState<ShotVersionsResponse | null>(null);

  const refreshTimeline = useCallback(async () => {
    const tl = await loadTimeline(filmId);
    setState((s) => ({ ...s, timeline: tl, status: 'idle' }));
  }, [filmId]);

  useEffect(() => {
    refreshTimeline();
  }, [refreshTimeline]);

  const handleSelectItem = async (itemId: string) => {
    const item = state.timeline?.timeline_items.find((i) => i.id === itemId);
    if (!item) return;
    setState((s) => ({ ...s, selectedTimelineItemId: itemId, status: 'loading' }));
    const vd = await loadVersions(item.shot.id);
    setVersionsData(vd);
    setState((s) => ({
      ...s,
      selectedShotVersions: vd.versions,
      activeVersionId: vd.active_version_id,
      status: 'idle',
    }));
  };

  const handleSelectVersion = async (shotId: string, versionId: string) => {
    setState((s) => ({ ...s, status: 'saving' }));
    const vd = await selectVersion(shotId, versionId);
    setVersionsData(vd);
    const updatedTimeline = state.timeline
      ? {
          ...state.timeline,
          timeline_items: state.timeline.timeline_items.map((item) =>
            item.shot.id === shotId
              ? { ...item, shot: { ...item.shot, active_version_id: versionId } }
              : item
          ),
        }
      : state.timeline;

    setState((s) => ({
      ...s,
      timeline: updatedTimeline,
      activeVersionId: vd.active_version_id,
      selectedShotVersions: vd.versions,
      status: 'idle',
    }));
  };

  const handleRegenerate = async (shotId: string) => {
    setState((s) => ({ ...s, status: 'saving' }));
    const vd = await regenerateShot(shotId, generationProvider);
    setVersionsData(vd);
    setState((s) => ({
      ...s,
      activeVersionId: vd.active_version_id,
      selectedShotVersions: vd.versions,
      status: 'idle',
    }));
  };

  const handleMove = async (itemId: string, direction: 'up' | 'down') => {
    const tl = await moveTimelineItem(filmId, itemId, direction);
    setState((s) => ({ ...s, timeline: tl }));
  };

  const handleDropReorder = async (targetItemId: string) => {
    if (!draggedItemId || !state.timeline || draggedItemId === targetItemId) return;
    const newPosition = state.timeline.timeline_items.find((item) => item.id === targetItemId)?.position;
    if (newPosition === undefined) return;

    const tl = await reorderTimelineItem(filmId, draggedItemId, newPosition);
    setState((s) => ({ ...s, timeline: tl }));
    setDraggedItemId(null);
  };

  const handleTimelinePatch = async (
    itemId: string,
    payload: { duration_seconds?: number; trim_start?: number; trim_end?: number | null }
  ) => {
    if (!state.timeline) return;
    const tl = await updateTimelineItem(filmId, itemId, payload);
    setState((s) => ({ ...s, timeline: tl }));
  };

  const handleRenderFilm = async () => {
    setState((s) => ({ ...s, status: 'saving', error: null }));
    try {
      const result = await renderFilm(filmId);
      setState((s) => ({ ...s, renderedVideoUrl: result.videoUrl, status: 'idle' }));
    } catch (error) {
      setState((s) => ({
        ...s,
        status: 'error',
        error: error instanceof Error ? error.message : 'Render failed',
      }));
    }
  };

  const handlePublishFilm = async () => {
    setState((s) => ({ ...s, status: 'saving', error: null }));
    try {
      const result = await publishFilm(
        filmId,
        publishTags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean)
      );
      setState((s) => ({ ...s, publishedFilmId: result.id, status: 'idle' }));
    } catch (error) {
      setState((s) => ({
        ...s,
        status: 'error',
        error: error instanceof Error ? error.message : 'Publish failed',
      }));
    }
  };

  const selectedItem = state.timeline?.timeline_items.find((i) => i.id === state.selectedTimelineItemId);

  const sortedItems = state.timeline
    ? [...state.timeline.timeline_items].sort((a, b) => a.position - b.position)
    : [];

  const selectedDuration = selectedItem?.duration_seconds ?? 1;
  const trimStart = selectedItem?.trim_start ?? 0;
  const trimEnd = selectedItem?.trim_end ?? null;
  const trimEndValue = trimEnd ?? selectedDuration;

  return (
    <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link href="/" style={{ color: '#9b8fff', textDecoration: 'none', fontSize: '14px' }}>← Home</Link>
          <h1 style={{ margin: 0, fontSize: '20px', color: '#e0e0ff' }}>Film Editor</h1>
          <span style={{ fontSize: '13px', color: '#888' }}>
            {state.status === 'loading' && '⏳ Loading...'}
            {state.status === 'saving' && '💾 Saving...'}
            {state.status === 'idle' && '✅ Ready'}
            {state.status === 'error' && '❌ Error'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            value={publishTags}
            onChange={(e) => setPublishTags(e.target.value)}
            aria-label="Publish tags"
            style={{ background: '#0d0d1e', border: '1px solid #3a3a6e', color: '#e0e0ff', borderRadius: '6px', padding: '8px 10px', fontSize: '13px', minWidth: '180px' }}
          />
          <button
            style={{ background: '#2d8a68', color: '#fff', border: 'none', borderRadius: '6px', padding: '10px 18px', fontSize: '14px', cursor: 'pointer', fontWeight: 600 }}
            onClick={handlePublishFilm}
          >
            Publish
          </button>
          <button
            style={{ background: '#7c6fff', color: '#fff', border: 'none', borderRadius: '6px', padding: '10px 20px', fontSize: '14px', cursor: 'pointer', fontWeight: 600 }}
            onClick={handleRenderFilm}
          >
            Render MP4
          </button>
        </div>
      </div>

      {state.error && (
        <p style={{ color: '#f88', marginBottom: '16px' }}>{state.error}</p>
      )}

      {(state.renderedVideoUrl || state.publishedFilmId) && (
        <section style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', border: '1px solid #2a2a4e', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
            <h2 style={{ margin: 0, fontSize: '15px', color: '#e0e0ff' }}>Distribution</h2>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {state.renderedVideoUrl && (
                <a href={state.renderedVideoUrl} target="_blank" rel="noreferrer" style={{ color: '#9b8fff', fontSize: '13px' }}>Open MP4</a>
              )}
              {state.publishedFilmId && (
                <Link href={`/film/${state.publishedFilmId}`} style={{ color: '#7ce0a6', fontSize: '13px' }}>
                  View public film →
                </Link>
              )}
            </div>
          </div>
          {state.renderedVideoUrl && (
            <video
              controls
              src={state.renderedVideoUrl}
              style={{ width: '100%', borderRadius: '8px', background: '#000' }}
            />
          )}
        </section>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
        <div style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', border: '1px solid #2a2a4e' }}>
          <h2 style={{ margin: '0 0 14px', fontSize: '15px', color: '#e0e0ff' }}>Timeline</h2>
          <p style={{ color: '#888', fontSize: '12px', marginTop: 0 }}>Drag clips to reorder, or use the arrows for precise moves.</p>
          {state.status === 'loading' && !state.timeline && (
            <p style={{ color: '#888', fontSize: '14px' }}>Loading timeline...</p>
          )}
          {sortedItems.map((item, idx) => (
            <div
              key={item.id}
              draggable
              onDragStart={() => setDraggedItemId(item.id)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDropReorder(item.id)}
              onClick={() => handleSelectItem(item.id)}
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                marginBottom: '8px',
                background: state.selectedTimelineItemId === item.id ? '#2d2b5e' : '#0f0f2e',
                border: state.selectedTimelineItemId === item.id ? '1px solid #7c6fff' : '1px solid #2a2a4e',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '12px', color: '#9b8fff', marginBottom: '4px' }}>Shot {idx + 1}</div>
                  <div style={{ fontSize: '13px', color: '#ccc', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                    {item.shot.prompt}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
                    <span style={{ fontSize: '12px', color: '#888' }}>{item.duration_seconds.toFixed(1)}s</span>
                    <span style={{ fontSize: '11px', color: '#666' }}>
                      trim {item.trim_start?.toFixed(1) ?? '0.0'} → {((item.trim_end ?? item.duration_seconds) || 0).toFixed(1)}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginLeft: '8px' }}>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleMove(item.id, 'up'); }}
                    disabled={idx === 0}
                    style={{ background: '#2a2a4e', border: 'none', color: idx === 0 ? '#555' : '#9b8fff', borderRadius: '4px', width: '24px', height: '24px', cursor: idx === 0 ? 'default' : 'pointer', fontSize: '12px' }}
                  >↑</button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleMove(item.id, 'down'); }}
                    disabled={idx === sortedItems.length - 1}
                    style={{ background: '#2a2a4e', border: 'none', color: idx === sortedItems.length - 1 ? '#555' : '#9b8fff', borderRadius: '4px', width: '24px', height: '24px', cursor: idx === sortedItems.length - 1 ? 'default' : 'pointer', fontSize: '12px' }}
                  >↓</button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', border: '1px solid #2a2a4e' }}>
          {!selectedItem ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#888', fontSize: '15px' }}>
              Select a shot from the timeline to view versions
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', gap: '12px', flexWrap: 'wrap' }}>
                <h2 style={{ margin: 0, fontSize: '15px', color: '#e0e0ff' }}>Shot Versions</h2>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <select
                    value={generationProvider}
                    onChange={(e) => setGenerationProvider(e.target.value as (typeof PROVIDERS)[number]['value'])}
                    style={{ background: '#0d0d1e', border: '1px solid #3a3a6e', color: '#e0e0ff', borderRadius: '6px', padding: '8px 10px', fontSize: '13px' }}
                  >
                    {PROVIDERS.map((provider) => (
                      <option key={provider.value} value={provider.value}>{provider.label}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => handleRegenerate(selectedItem.shot.id)}
                    disabled={state.status === 'saving'}
                    style={{ background: '#7c6fff', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: state.status === 'saving' ? 'wait' : 'pointer' }}
                  >
                    {state.status === 'saving' ? 'Generating...' : '+ Generate clip'}
                  </button>
                </div>
              </div>
              <p style={{ color: '#888', fontSize: '13px', marginBottom: '12px' }}>
                Prompt: <em style={{ color: '#ccc' }}>{selectedItem.shot.prompt}</em>
              </p>

              <div style={{ background: '#0f0f1e', border: '1px solid #2a2a4e', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '12px', alignItems: 'center' }}>
                  <div>
                    <label style={{ display: 'block', color: '#aaa', fontSize: '12px', marginBottom: '6px' }}>Trim start</label>
                    <input
                      type="range"
                      min={0}
                      max={Math.max(selectedDuration - 0.2, 0.2)}
                      step={0.1}
                      value={trimStart}
                      onChange={(e) => handleTimelinePatch(selectedItem.id, { trim_start: Number(e.target.value) })}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div style={{ color: '#ccc', fontSize: '13px' }}>{trimStart.toFixed(1)}s</div>
                  <div>
                    <label style={{ display: 'block', color: '#aaa', fontSize: '12px', marginBottom: '6px' }}>Trim end</label>
                    <input
                      type="range"
                      min={Math.min(trimStart + 0.2, selectedDuration)}
                      max={selectedDuration}
                      step={0.1}
                      value={trimEndValue}
                      onChange={(e) => handleTimelinePatch(selectedItem.id, { trim_end: Number(e.target.value) })}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div style={{ color: '#ccc', fontSize: '13px' }}>{trimEndValue.toFixed(1)}s</div>
                </div>
              </div>

              {state.status === 'loading' ? (
                <p style={{ color: '#888' }}>Loading versions...</p>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px' }}>
                  {state.selectedShotVersions.map((version) => (
                    <div
                      key={version.id}
                      style={{
                        borderRadius: '6px',
                        overflow: 'hidden',
                        border: state.activeVersionId === version.id ? '2px solid #7c6fff' : '2px solid #2a2a4e',
                        background: '#0f0f1e',
                      }}
                    >
                      <div style={{ position: 'relative', paddingTop: '56.25%' }}>
                        {version.status === 'ready' ? (
                          <img
                            src={version.image_url}
                            alt="Version"
                            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                          />
                        ) : (
                          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: '13px' }}>
                            {version.status === 'pending' ? '⏳ Pending' : version.status === 'processing' ? '⚙️ Processing' : '❌ Failed'}
                          </div>
                        )}
                      </div>
                      <div style={{ padding: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                          <span style={{ background: '#23234a', color: '#d6d2ff', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>
                            {(version.provider ?? 'runway').replace(/-/g, ' ')}
                          </span>
                          {state.activeVersionId === version.id && (
                            <span style={{ background: '#7c6fff', color: '#fff', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Active</span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', color: '#888', marginTop: '6px' }}>
                          {new Date(version.created_at).toLocaleString()}
                        </div>
                        {version.video_url && (
                          <a
                            href={version.video_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{ display: 'inline-block', marginTop: '8px', color: '#9b8fff', fontSize: '12px' }}
                          >
                            Preview clip ↗
                          </a>
                        )}
                        <button
                          onClick={() => handleSelectVersion(selectedItem.shot.id, version.id)}
                          style={{ marginTop: '8px', width: '100%', background: state.activeVersionId === version.id ? '#2d8a68' : '#2a2a4e', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px', fontSize: '12px', cursor: 'pointer' }}
                        >
                          {state.activeVersionId === version.id ? 'Selected in edit' : 'Use this version'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
