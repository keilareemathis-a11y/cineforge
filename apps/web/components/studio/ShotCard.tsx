'use client';
import { useState } from 'react';
import type { Shot, ShotVersion } from '../../lib/store';

interface ShotCardProps {
  shot: Shot;
  versions: ShotVersion[];
  onGenerate: (shotId: string) => Promise<void>;
  onSelectVersion: (shotId: string, versionId: string) => Promise<void>;
  onAddToTimeline: (shotId: string) => Promise<void>;
  onDelete: (shotId: string) => Promise<void>;
  isGenerating: boolean;
}

export default function ShotCard({
  shot,
  versions,
  onGenerate,
  onSelectVersion,
  onAddToTimeline,
  onDelete,
  isGenerating,
}: ShotCardProps) {
  const [showVersions, setShowVersions] = useState(false);
  const activeVersion = versions.find((v) => v.id === shot.active_version_id);

  return (
    <article
      style={{
        background: '#16162a',
        border: '1px solid #2a2a4a',
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      {/* Thumbnail */}
      <div
        style={{
          width: '100%',
          aspectRatio: '16/9',
          background: '#0d0d1e',
          position: 'relative',
          overflow: 'hidden',
        }}
        aria-hidden="true"
      >
        {activeVersion?.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={activeVersion.image_url}
            alt={`Generated visual for: ${shot.prompt}`}
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
              color: '#444',
              fontSize: '13px',
            }}
          >
            No image yet
          </div>
        )}
        {isGenerating && (
          <div
            role="status"
            aria-label="Generating image…"
            style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(13,13,30,0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#7c6fff',
              fontSize: '14px',
            }}
          >
            Generating…
          </div>
        )}
      </div>

      {/* Details */}
      <div style={{ padding: '14px' }}>
        <h3
          style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#e0e0ff' }}
        >
          {shot.title}
        </h3>
        <p
          style={{
            margin: '6px 0 0',
            fontSize: '12px',
            color: '#888',
            lineHeight: 1.5,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {shot.prompt}
        </p>

        {/* Version badge */}
        <p style={{ margin: '8px 0 0', fontSize: '11px', color: '#555' }}>
          {versions.length} version{versions.length !== 1 ? 's' : ''}
          {activeVersion ? ` · v${activeVersion.version_number} active` : ''}
        </p>

        {/* Actions */}
        <div
          style={{
            display: 'flex',
            gap: '6px',
            flexWrap: 'wrap',
            marginTop: '10px',
          }}
        >
          <button
            type="button"
            onClick={() => onGenerate(shot.id)}
            disabled={isGenerating}
            aria-label={`Generate new image for shot "${shot.title}"`}
            style={{
              background: '#7c6fff',
              color: '#fff',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '6px',
              cursor: isGenerating ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              opacity: isGenerating ? 0.6 : 1,
            }}
          >
            {versions.length === 0 ? 'Generate' : 'Regenerate'}
          </button>

          {versions.length > 0 && (
            <button
              type="button"
              onClick={() => setShowVersions((v) => !v)}
              aria-expanded={showVersions}
              aria-label={`${showVersions ? 'Hide' : 'Show'} versions for shot "${shot.title}"`}
              style={{
                background: 'transparent',
                color: '#7c6fff',
                border: '1px solid #7c6fff',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              Versions
            </button>
          )}

          <button
            type="button"
            onClick={() => onAddToTimeline(shot.id)}
            aria-label={`Add shot "${shot.title}" to timeline`}
            style={{
              background: 'transparent',
              color: '#4caf8a',
              border: '1px solid #4caf8a',
              padding: '6px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            + Timeline
          </button>

          <button
            type="button"
            onClick={() => onDelete(shot.id)}
            aria-label={`Delete shot "${shot.title}"`}
            style={{
              background: 'transparent',
              color: '#e05555',
              border: '1px solid #e05555',
              padding: '6px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              marginLeft: 'auto',
            }}
          >
            Delete
          </button>
        </div>

        {/* Versions panel */}
        {showVersions && (
          <ul
            style={{
              marginTop: '12px',
              padding: 0,
              listStyle: 'none',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
            aria-label={`Versions for shot "${shot.title}"`}
          >
            {versions.map((v) => (
              <li
                key={v.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: '#0d0d1e',
                  borderRadius: '6px',
                  padding: '8px',
                  border:
                    v.id === shot.active_version_id
                      ? '1px solid #7c6fff'
                      : '1px solid #2a2a4a',
                }}
              >
                {v.image_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={v.image_url}
                    alt={`Version ${v.version_number}`}
                    width={60}
                    height={34}
                    style={{ objectFit: 'cover', borderRadius: '4px', flexShrink: 0 }}
                  />
                )}
                <div style={{ flexGrow: 1, minWidth: 0 }}>
                  <p style={{ margin: 0, fontSize: '12px', color: '#e0e0ff', fontWeight: 600 }}>
                    v{v.version_number}
                    {v.id === shot.active_version_id && (
                      <span
                        style={{
                          marginLeft: '6px',
                          fontSize: '10px',
                          background: '#7c6fff',
                          padding: '2px 6px',
                          borderRadius: '4px',
                        }}
                      >
                        active
                      </span>
                    )}
                  </p>
                  <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#555' }}>
                    {v.provider} ·{' '}
                    {new Date(v.created_at).toLocaleString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                {v.id !== shot.active_version_id && (
                  <button
                    type="button"
                    onClick={() => onSelectVersion(shot.id, v.id)}
                    aria-label={`Set version ${v.version_number} as active`}
                    style={{
                      background: 'transparent',
                      color: '#7c6fff',
                      border: '1px solid #7c6fff',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '11px',
                      flexShrink: 0,
                    }}
                  >
                    Use
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
