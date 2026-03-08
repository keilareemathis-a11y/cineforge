'use client';
import { useState, useEffect, useCallback } from 'react';
import type { FilmTimeline, ShotVersionsResponse } from '../../types/platform';
import type { EditorState } from '../../types/editor';
import {
  loadTimeline,
  loadVersions,
  selectVersion,
  regenerateShot,
  moveTimelineItem,
  updateDuration,
} from '../../lib/api/editor';
import Link from 'next/link';

interface EditorClientProps {
  filmId: string;
}

export default function EditorClient({ filmId }: EditorClientProps) {
  const [state, setState] = useState<EditorState>({
    filmId,
    timeline: null,
    selectedTimelineItemId: null,
    selectedShotVersions: [],
    activeVersionId: null,
    status: 'loading',
    error: null,
  });

  const [_versionsData, setVersionsData] = useState<ShotVersionsResponse | null>(null);

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
    setState((s) => ({ ...s, selectedShotVersions: vd.versions, activeVersionId: vd.active_version_id, status: 'idle' }));
  };

  const handleSelectVersion = async (shotId: string, versionId: string) => {
    setState((s) => ({ ...s, status: 'saving' }));
    const vd = await selectVersion(shotId, versionId);
    setVersionsData(vd);
    setState((s) => ({ ...s, activeVersionId: vd.active_version_id, selectedShotVersions: vd.versions, status: 'idle' }));
  };

  const handleRegenerate = async (shotId: string) => {
    setState((s) => ({ ...s, status: 'saving' }));
    const vd = await regenerateShot(shotId);
    setVersionsData(vd);
    setState((s) => ({ ...s, selectedShotVersions: vd.versions, status: 'idle' }));
  };

  const handleMove = async (itemId: string, direction: 'up' | 'down') => {
    const tl = await moveTimelineItem(filmId, itemId, direction);
    setState((s) => ({ ...s, timeline: tl }));
  };

  const handleDurationChange = async (itemId: string, duration: number) => {
    if (!state.timeline) return;
    const updated: FilmTimeline = {
      ...state.timeline,
      timeline_items: state.timeline.timeline_items.map((i) =>
        i.id === itemId ? { ...i, duration_seconds: duration } : i
      ),
    };
    setState((s) => ({ ...s, timeline: updated }));
    await updateDuration(filmId, itemId, duration);
  };

  const selectedItem = state.timeline?.timeline_items.find((i) => i.id === state.selectedTimelineItemId);

  const sortedItems = state.timeline
    ? [...state.timeline.timeline_items].sort((a, b) => a.position - b.position)
    : [];

  return (
    <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
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
        <button
          style={{ background: '#7c6fff', color: '#fff', border: 'none', borderRadius: '6px', padding: '10px 20px', fontSize: '14px', cursor: 'pointer', fontWeight: 600 }}
          onClick={() => alert('Publish flow coming soon!')}
        >
          Publish
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
        {/* Timeline */}
        <div style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', border: '1px solid #2a2a4e' }}>
          <h2 style={{ margin: '0 0 14px', fontSize: '15px', color: '#e0e0ff' }}>Timeline</h2>
          {state.status === 'loading' && !state.timeline && (
            <p style={{ color: '#888', fontSize: '14px' }}>Loading timeline...</p>
          )}
          {sortedItems.map((item, idx) => (
            <div
              key={item.id}
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
                    <span style={{ fontSize: '12px', color: '#888' }}>{item.duration_seconds}s</span>
                    <input
                      type="number"
                      value={item.duration_seconds}
                      min={1}
                      max={30}
                      onChange={(e) => handleDurationChange(item.id, Number(e.target.value))}
                      onClick={(e) => e.stopPropagation()}
                      style={{ width: '50px', background: '#0d0d1e', border: '1px solid #3a3a6e', color: '#e0e0ff', borderRadius: '4px', padding: '2px 4px', fontSize: '12px' }}
                    />
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

        {/* Version Panel */}
        <div style={{ background: '#1a1a2e', borderRadius: '8px', padding: '16px', border: '1px solid #2a2a4e' }}>
          {!selectedItem ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#888', fontSize: '15px' }}>
              Select a shot from the timeline to view versions
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ margin: 0, fontSize: '15px', color: '#e0e0ff' }}>Shot Versions</h2>
                <button
                  onClick={() => handleRegenerate(selectedItem.shot.id)}
                  disabled={state.status === 'saving'}
                  style={{ background: '#7c6fff', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: state.status === 'saving' ? 'wait' : 'pointer' }}
                >
                  {state.status === 'saving' ? 'Generating...' : '+ Regenerate'}
                </button>
              </div>
              <p style={{ color: '#888', fontSize: '13px', marginBottom: '12px' }}>
                Prompt: <em style={{ color: '#ccc' }}>{selectedItem.shot.prompt}</em>
              </p>
              {state.status === 'loading' ? (
                <p style={{ color: '#888' }}>Loading versions...</p>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                  {state.selectedShotVersions.map((version) => (
                    <div
                      key={version.id}
                      onClick={() => handleSelectVersion(selectedItem.shot.id, version.id)}
                      style={{
                        borderRadius: '6px',
                        overflow: 'hidden',
                        border: state.activeVersionId === version.id ? '2px solid #7c6fff' : '2px solid #2a2a4e',
                        cursor: 'pointer',
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
                          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: '13px' }}>
                            {version.status === 'pending' ? '⏳ Pending' : version.status === 'processing' ? '⚙️ Processing' : '❌ Failed'}
                          </div>
                        )}
                      </div>
                      <div style={{ padding: '8px' }}>
                        {state.activeVersionId === version.id && (
                          <span style={{ background: '#7c6fff', color: '#fff', fontSize: '11px', padding: '2px 6px', borderRadius: '4px' }}>Active</span>
                        )}
                        <div style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
                          {new Date(version.created_at).toLocaleString()}
                        </div>
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
