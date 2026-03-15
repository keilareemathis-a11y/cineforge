'use client';
import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import type { Project, Timeline, Clip, Shot, ShotVersion } from '../../../../lib/store';

interface ClipWithDetails extends Clip {
  shot: Shot | null;
  version: ShotVersion | null;
}

export default function TimelinePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [clips, setClips] = useState<ClipWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [projRes, tlRes, shotsRes] = await Promise.all([
        fetch(`/api/projects/${projectId}`),
        fetch(`/api/timeline/${projectId}`),
        fetch(`/api/shots?project_id=${projectId}`),
      ]);

      const proj: Project = projRes.ok ? await projRes.json() : null;
      const tl: Timeline = tlRes.ok ? await tlRes.json() : { clips: [] };
      const shots: Shot[] = shotsRes.ok ? await shotsRes.json() : [];

      const shotsMap = new Map(shots.map((s) => [s.id, s]));

      // Load versions for each shot that has an active_version_id
      const versionsMap = new Map<string, ShotVersion>();
      await Promise.all(
        shots
          .filter((s) => s.active_version_id)
          .map(async (s) => {
            const vRes = await fetch(`/api/shots/${s.id}/versions`);
            if (!vRes.ok) return;
            const vData = await vRes.json();
            const active = (vData.versions as ShotVersion[]).find(
              (v) => v.id === s.active_version_id
            );
            if (active) versionsMap.set(s.id, active);
          })
      );

      const enrichedClips: ClipWithDetails[] = (tl.clips ?? []).map((clip) => ({
        ...clip,
        shot: shotsMap.get(clip.shot_id) ?? null,
        version: clip.version_id
          ? versionsMap.get(clip.shot_id) ?? null
          : shotsMap.get(clip.shot_id)
          ? versionsMap.get(clip.shot_id) ?? null
          : null,
      }));

      setProject(proj);
      setTimeline(tl);
      setClips(enrichedClips);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRemoveClip = async (clipId: string) => {
    const res = await fetch(`/api/timeline/${projectId}/clips/${clipId}`, {
      method: 'DELETE',
    });
    if (res.ok) {
      setClips((prev) => prev.filter((c) => c.id !== clipId).map((c, i) => ({ ...c, position: i })));
    }
  };

  const handleDragStart = (index: number) => {
    setDragIndex(index);
  };

  const handleDrop = async (targetIndex: number) => {
    if (dragIndex === null || dragIndex === targetIndex) {
      setDragIndex(null);
      return;
    }
    const reordered = [...clips];
    const [moved] = reordered.splice(dragIndex, 1);
    reordered.splice(targetIndex, 0, moved);
    const updated = reordered.map((c, i) => ({ ...c, position: i }));
    setClips(updated);
    setDragIndex(null);

    await fetch(`/api/timeline/${projectId}/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_ids: updated.map((c) => c.id) }),
    });
  };

  const handleExport = async () => {
    setExporting(true);
    setExportResult(null);
    try {
      const res = await fetch(`/api/export/${projectId}`, { method: 'POST' });
      const data = await res.json();
      setExportResult(
        `Export queued: ${data.clip_count} clip(s), ${data.total_duration_seconds}s total. ${data.message}`
      );
    } catch {
      setExportResult('Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const totalDuration = clips.reduce((sum, c) => sum + c.duration, 0);

  if (loading) {
    return (
      <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
        <p role="status" aria-live="polite" style={{ color: '#888' }}>
          Loading timeline…
        </p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', gap: '16px', marginBottom: '8px', flexWrap: 'wrap' }}>
          <Link
            href={`/projects/${projectId}`}
            style={{ color: '#7c6fff', fontSize: '13px', textDecoration: 'none' }}
          >
            ← {project?.name ?? 'Project'}
          </Link>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <h1
              style={{ margin: 0, fontSize: '26px', fontWeight: 800, color: '#e0e0ff' }}
            >
              Timeline
            </h1>
            <p style={{ margin: '4px 0 0', color: '#888', fontSize: '14px' }}>
              {clips.length} clip{clips.length !== 1 ? 's' : ''} · {totalDuration}s total
            </p>
          </div>
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting || clips.length === 0}
            aria-label="Export film (stub)"
            style={{
              background: exporting ? '#333' : '#4caf8a',
              color: '#fff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              cursor: exporting || clips.length === 0 ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              fontSize: '14px',
              opacity: clips.length === 0 ? 0.5 : 1,
            }}
          >
            {exporting ? 'Exporting…' : '⬇ Export Film'}
          </button>
        </div>
      </div>

      {/* Export result */}
      {exportResult && (
        <div
          role="status"
          aria-live="polite"
          style={{
            background: '#1e2a3a',
            border: '1px solid #4a7cbf',
            borderRadius: '8px',
            padding: '12px 16px',
            marginBottom: '20px',
            color: '#a0c0ff',
            fontSize: '14px',
          }}
        >
          {exportResult}
        </div>
      )}

      {/* Timeline */}
      {clips.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 0',
            color: '#888',
            border: '2px dashed #2a2a4a',
            borderRadius: '12px',
          }}
        >
          <p style={{ fontSize: '16px', marginBottom: '8px' }}>
            Timeline is empty.
          </p>
          <p style={{ fontSize: '13px', color: '#555' }}>
            Go to your{' '}
            <Link
              href={`/projects/${projectId}`}
              style={{ color: '#7c6fff', textDecoration: 'none' }}
            >
              project shots
            </Link>{' '}
            and click <strong>+ Timeline</strong> to add clips.
          </p>
        </div>
      ) : (
        <>
          <p style={{ fontSize: '12px', color: '#555', marginBottom: '12px' }}>
            Drag clips to reorder
          </p>
          <ol
            aria-label="Timeline clips"
            style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}
          >
            {clips.map((clip, index) => (
              <li
                key={clip.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDrop(index)}
                style={{
                  background: dragIndex === index ? '#1e1e3a' : '#16162a',
                  border: '1px solid #2a2a4a',
                  borderRadius: '8px',
                  padding: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: 'grab',
                  opacity: dragIndex === index ? 0.5 : 1,
                  transition: 'opacity 0.15s',
                }}
                aria-label={`Clip ${index + 1}: ${clip.shot?.title ?? 'Unknown shot'}`}
              >
                {/* Position */}
                <span
                  style={{
                    fontSize: '12px',
                    color: '#555',
                    minWidth: '24px',
                    textAlign: 'center',
                  }}
                  aria-hidden="true"
                >
                  {index + 1}
                </span>

                {/* Thumbnail */}
                <div
                  style={{
                    width: '80px',
                    height: '45px',
                    background: '#0d0d1e',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    flexShrink: 0,
                  }}
                  aria-hidden="true"
                >
                  {clip.version?.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={clip.version.image_url}
                      alt=""
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#333',
                        fontSize: '10px',
                      }}
                    >
                      No img
                    </div>
                  )}
                </div>

                {/* Details */}
                <div style={{ flexGrow: 1, minWidth: 0 }}>
                  <p
                    style={{
                      margin: 0,
                      fontSize: '14px',
                      fontWeight: 600,
                      color: '#e0e0ff',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {clip.shot?.title ?? 'Unknown shot'}
                  </p>
                  <p
                    style={{
                      margin: '3px 0 0',
                      fontSize: '12px',
                      color: '#888',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {clip.shot?.prompt ?? ''}
                  </p>
                </div>

                {/* Duration */}
                <span
                  style={{
                    fontSize: '12px',
                    color: '#7c6fff',
                    flexShrink: 0,
                    background: '#1a1a3a',
                    padding: '3px 8px',
                    borderRadius: '4px',
                  }}
                >
                  {clip.duration}s
                </span>

                {/* Remove */}
                <button
                  type="button"
                  onClick={() => handleRemoveClip(clip.id)}
                  aria-label={`Remove clip "${clip.shot?.title ?? 'Unknown'}"`}
                  style={{
                    background: 'transparent',
                    color: '#e05555',
                    border: '1px solid #e05555',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    flexShrink: 0,
                  }}
                >
                  ✕
                </button>
              </li>
            ))}
          </ol>

          {/* Visual timeline bar */}
          <div
            aria-hidden="true"
            style={{
              marginTop: '24px',
              background: '#0d0d1e',
              borderRadius: '8px',
              padding: '12px',
              border: '1px solid #2a2a4a',
            }}
          >
            <p style={{ margin: '0 0 8px', fontSize: '12px', color: '#555' }}>
              Timeline preview
            </p>
            <div style={{ display: 'flex', height: '40px', gap: '2px' }}>
              {clips.map((clip) => (
                <div
                  key={clip.id}
                  title={clip.shot?.title ?? 'Unknown'}
                  style={{
                    flex: clip.duration,
                    background: '#7c6fff',
                    borderRadius: '4px',
                    minWidth: '20px',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {clip.version?.image_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={clip.version.image_url}
                      alt=""
                      style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.7 }}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </main>
  );
}
