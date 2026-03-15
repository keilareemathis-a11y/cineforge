'use client';
import { useState } from 'react';
import type { Shot } from '../../lib/store';

interface CreateShotFormProps {
  projectId: string;
  onCreated: (shot: Shot) => void;
}

export default function CreateShotForm({ projectId, onCreated }: CreateShotFormProps) {
  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !prompt.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/shots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, title, prompt }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error ?? 'Failed to create shot');
      }
      const shot: Shot = await res.json();
      onCreated(shot);
      setTitle('');
      setPrompt('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      aria-label="Create new shot"
      style={{
        background: '#16162a',
        border: '1px solid #2a2a4a',
        borderRadius: '12px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#e0e0ff' }}>
        New Shot
      </h3>

      {error && (
        <p role="alert" style={{ margin: 0, color: '#e05555', fontSize: '13px' }}>
          {error}
        </p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <label
          htmlFor="shot-title"
          style={{ fontSize: '13px', color: '#aaa', fontWeight: 600 }}
        >
          Shot title
        </label>
        <input
          id="shot-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Opening wide shot"
          required
          style={{
            background: '#0d0d1e',
            border: '1px solid #2a2a4a',
            borderRadius: '6px',
            color: '#e0e0ff',
            fontSize: '14px',
            padding: '8px 12px',
            outline: 'none',
          }}
        />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <label
          htmlFor="shot-prompt"
          style={{ fontSize: '13px', color: '#aaa', fontWeight: 600 }}
        >
          Prompt
        </label>
        <textarea
          id="shot-prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the scene, mood, camera angle, lighting…"
          required
          rows={3}
          style={{
            background: '#0d0d1e',
            border: '1px solid #2a2a4a',
            borderRadius: '6px',
            color: '#e0e0ff',
            fontSize: '14px',
            padding: '8px 12px',
            outline: 'none',
            resize: 'vertical',
            fontFamily: 'inherit',
          }}
        />
      </div>

      <button
        type="submit"
        disabled={loading || !title.trim() || !prompt.trim()}
        style={{
          background: '#7c6fff',
          color: '#fff',
          border: 'none',
          padding: '9px 18px',
          borderRadius: '6px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: '14px',
          fontWeight: 600,
          opacity: loading ? 0.7 : 1,
          alignSelf: 'flex-start',
        }}
      >
        {loading ? 'Creating…' : 'Create Shot'}
      </button>
    </form>
  );
}
