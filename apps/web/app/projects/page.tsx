'use client';
import { useState, useEffect } from 'react';
import type { Project } from '../../lib/store';
import ProjectCard from '../../components/studio/ProjectCard';
import Link from 'next/link';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/projects')
      .then((r) => r.json())
      .then((data: Project[]) => setProjects(data))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, description: newDesc }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error ?? 'Failed to create project');
      }
      const project: Project = await res.json();
      setProjects((prev) => [project, ...prev]);
      setNewName('');
      setNewDesc('');
      setShowForm(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setCreating(false);
    }
  };

  return (
    <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '32px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <Link
            href="/"
            style={{ color: '#7c6fff', fontSize: '13px', textDecoration: 'none' }}
            aria-label="Back to home"
          >
            ← Home
          </Link>
          <h1
            style={{
              margin: '8px 0 4px',
              fontSize: '26px',
              fontWeight: 800,
              color: '#e0e0ff',
            }}
          >
            Projects
          </h1>
          <p style={{ margin: 0, color: '#888', fontSize: '14px' }}>
            Manage your AI filmmaking projects
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          aria-expanded={showForm}
          style={{
            background: '#7c6fff',
            color: '#fff',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '14px',
          }}
        >
          {showForm ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          aria-label="Create new project"
          style={{
            background: '#16162a',
            border: '1px solid #2a2a4a',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '32px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <h2
            style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#e0e0ff' }}
          >
            New Project
          </h2>
          {error && (
            <p role="alert" style={{ margin: 0, color: '#e05555', fontSize: '13px' }}>
              {error}
            </p>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label
              htmlFor="project-name"
              style={{ fontSize: '13px', color: '#aaa', fontWeight: 600 }}
            >
              Project name <span aria-hidden="true">*</span>
            </label>
            <input
              id="project-name"
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="My Sci-Fi Short"
              required
              style={{
                background: '#0d0d1e',
                border: '1px solid #2a2a4a',
                borderRadius: '6px',
                color: '#e0e0ff',
                fontSize: '14px',
                padding: '9px 12px',
                outline: 'none',
              }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label
              htmlFor="project-desc"
              style={{ fontSize: '13px', color: '#aaa', fontWeight: 600 }}
            >
              Description (optional)
            </label>
            <textarea
              id="project-desc"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="A short description of your film…"
              rows={2}
              style={{
                background: '#0d0d1e',
                border: '1px solid #2a2a4a',
                borderRadius: '6px',
                color: '#e0e0ff',
                fontSize: '14px',
                padding: '9px 12px',
                outline: 'none',
                resize: 'vertical',
                fontFamily: 'inherit',
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="submit"
              disabled={creating || !newName.trim()}
              style={{
                background: '#7c6fff',
                color: '#fff',
                border: 'none',
                padding: '9px 18px',
                borderRadius: '6px',
                cursor: creating ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '14px',
                opacity: creating ? 0.7 : 1,
              }}
            >
              {creating ? 'Creating…' : 'Create Project'}
            </button>
          </div>
        </form>
      )}

      {/* Project grid */}
      {loading ? (
        <p
          role="status"
          aria-live="polite"
          style={{ color: '#888', textAlign: 'center', padding: '40px 0' }}
        >
          Loading projects…
        </p>
      ) : projects.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 0',
            color: '#888',
          }}
        >
          <p style={{ fontSize: '16px', marginBottom: '16px' }}>
            No projects yet.
          </p>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            style={{
              background: '#7c6fff',
              color: '#fff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '14px',
            }}
          >
            Create your first project
          </button>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '16px',
          }}
          role="list"
          aria-label="Projects"
        >
          {projects.map((project) => (
            <div key={project.id} role="listitem">
              <ProjectCard project={project} />
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
