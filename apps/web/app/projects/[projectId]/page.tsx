'use client';
import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import type { Project, Shot, ShotVersion } from '../../../lib/store';
import ShotCard from '../../../components/studio/ShotCard';
import CreateShotForm from '../../../components/studio/CreateShotForm';

interface ShotWithVersions {
  shot: Shot;
  versions: ShotVersion[];
}

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [shotsData, setShotsData] = useState<ShotWithVersions[]>([]);
  const [loading, setLoading] = useState(true);
  const [generatingIds, setGeneratingIds] = useState<Set<string>>(new Set());
  const [timelineMsg, setTimelineMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [projRes, shotsRes] = await Promise.all([
        fetch(`/api/projects/${projectId}`),
        fetch(`/api/shots?project_id=${projectId}`),
      ]);
      if (!projRes.ok) throw new Error('Project not found');
      const proj: Project = await projRes.json();
      const shots: Shot[] = shotsRes.ok ? await shotsRes.json() : [];

      const shotsWithVersions = await Promise.all(
        shots.map(async (shot) => {
          const vRes = await fetch(`/api/shots/${shot.id}/versions`);
          const vData = vRes.ok
            ? await vRes.json()
            : { versions: [], active_version_id: null };
          return {
            shot: { ...shot, active_version_id: vData.active_version_id },
            versions: vData.versions as ShotVersion[],
          };
        })
      );

      setProject(proj);
      setShotsData(shotsWithVersions);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load project');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleShotCreated = async (shot: Shot) => {
    const vRes = await fetch(`/api/shots/${shot.id}/versions`);
    const vData = vRes.ok
      ? await vRes.json()
      : { versions: [], active_version_id: null };
    setShotsData((prev) => [
      { shot: { ...shot, active_version_id: vData.active_version_id }, versions: [] },
      ...prev,
    ]);
  };

  const handleGenerate = async (shotId: string) => {
    setGeneratingIds((s) => { const n = new Set(s); n.add(shotId); return n; });
    try {
      const res = await fetch(`/api/shots/${shotId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error ?? 'Generation failed');
      }
      const version: ShotVersion = await res.json();
      setShotsData((prev) =>
        prev.map((sd) =>
          sd.shot.id === shotId
            ? {
                shot: { ...sd.shot, active_version_id: version.id },
                versions: [version, ...sd.versions],
              }
            : sd
        )
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGeneratingIds((s) => {
        const next = new Set(s);
        next.delete(shotId);
        return next;
      });
    }
  };

  const handleSelectVersion = async (shotId: string, versionId: string) => {
    const res = await fetch(
      `/api/shots/${shotId}/versions/${versionId}/select`,
      { method: 'POST' }
    );
    if (!res.ok) return;
    const data = await res.json();
    setShotsData((prev) =>
      prev.map((sd) =>
        sd.shot.id === shotId
          ? { ...sd, shot: { ...sd.shot, active_version_id: data.active_version_id } }
          : sd
      )
    );
  };

  const handleAddToTimeline = async (shotId: string) => {
    const res = await fetch(`/api/timeline/${projectId}/clips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shot_id: shotId }),
    });
    if (res.ok) {
      setTimelineMsg('Shot added to timeline!');
      setTimeout(() => setTimelineMsg(null), 3000);
    }
  };

  const handleDeleteShot = async (shotId: string) => {
    if (!confirm('Delete this shot and all its versions?')) return;
    const res = await fetch(`/api/shots/${shotId}`, { method: 'DELETE' });
    if (res.ok) {
      setShotsData((prev) => prev.filter((sd) => sd.shot.id !== shotId));
    }
  };

  if (loading) {
    return (
      <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
        <p role="status" aria-live="polite" style={{ color: '#888' }}>
          Loading project…
        </p>
      </main>
    );
  }

  if (error || !project) {
    return (
      <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
        <p role="alert" style={{ color: '#e05555' }}>
          {error ?? 'Project not found'}
        </p>
        <Link href="/projects" style={{ color: '#7c6fff', fontSize: '14px' }}>
          ← Back to projects
        </Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <Link
          href="/projects"
          style={{ color: '#7c6fff', fontSize: '13px', textDecoration: 'none' }}
        >
          ← Projects
        </Link>
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginTop: '8px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <h1
              style={{ margin: 0, fontSize: '26px', fontWeight: 800, color: '#e0e0ff' }}
            >
              {project.name}
            </h1>
            {project.description && (
              <p style={{ margin: '6px 0 0', color: '#888', fontSize: '14px' }}>
                {project.description}
              </p>
            )}
          </div>
          <Link
            href={`/projects/${projectId}/timeline`}
            style={{
              background: '#7c6fff',
              color: '#fff',
              padding: '10px 20px',
              borderRadius: '8px',
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '14px',
            }}
          >
            Open Timeline →
          </Link>
        </div>
      </div>

      {/* Toast */}
      {timelineMsg && (
        <div
          role="status"
          aria-live="polite"
          style={{
            background: '#1e3a2a',
            border: '1px solid #4caf8a',
            borderRadius: '8px',
            padding: '12px 16px',
            marginBottom: '20px',
            color: '#4caf8a',
            fontSize: '14px',
          }}
        >
          {timelineMsg}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 2fr',
          gap: '32px',
          alignItems: 'start',
        }}
      >
        {/* Create shot form */}
        <div>
          <CreateShotForm
            projectId={projectId}
            onCreated={handleShotCreated}
          />
        </div>

        {/* Shot grid */}
        <div>
          <h2
            style={{
              margin: '0 0 16px',
              fontSize: '18px',
              fontWeight: 700,
              color: '#e0e0ff',
            }}
          >
            Shots ({shotsData.length})
          </h2>
          {shotsData.length === 0 ? (
            <p style={{ color: '#888', fontSize: '14px' }}>
              No shots yet. Create your first shot to get started.
            </p>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
                gap: '16px',
              }}
              aria-label="Project shots"
            >
              {shotsData.map(({ shot, versions }) => (
                <ShotCard
                  key={shot.id}
                  shot={shot}
                  versions={versions}
                  onGenerate={handleGenerate}
                  onSelectVersion={handleSelectVersion}
                  onAddToTimeline={handleAddToTimeline}
                  onDelete={handleDeleteShot}
                  isGenerating={generatingIds.has(shot.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
