'use client';
import Link from 'next/link';
import Image from 'next/image';
import type { PublishedFilm } from '../../types/platform';

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatCount(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

interface FilmCardProps {
  film: PublishedFilm;
}

export default function FilmCard({ film }: FilmCardProps) {
  return (
    <Link href={`/film/${film.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
      <div style={{
        borderRadius: '8px',
        overflow: 'hidden',
        background: '#1a1a2e',
        border: '1px solid #2a2a4e',
        transition: 'transform 0.2s',
        cursor: 'pointer',
      }}>
        <div style={{ position: 'relative', paddingTop: '56.25%', background: '#0f0f1e' }}>
          <Image
            src={film.thumbnail_url}
            alt={film.title}
            fill
            style={{ objectFit: 'cover' }}
          />
          <span style={{
            position: 'absolute',
            bottom: '8px',
            right: '8px',
            background: 'rgba(0,0,0,0.8)',
            color: '#fff',
            fontSize: '12px',
            padding: '2px 6px',
            borderRadius: '4px',
          }}>
            {formatDuration(film.duration_seconds)}
          </span>
        </div>
        <div style={{ padding: '12px' }}>
          <h3 style={{ margin: '0 0 4px', fontSize: '15px', fontWeight: 600, color: '#e0e0ff' }}>
            {film.title}
          </h3>
          <Link
            href={`/creator/${film.creator.handle}`}
            onClick={(e) => e.stopPropagation()}
            style={{ fontSize: '13px', color: '#9b8fff', textDecoration: 'none' }}
          >
            {film.creator.display_name}
          </Link>
          <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '12px', color: '#888' }}>
            <span>👁 {formatCount(film.view_count)}</span>
            <span>♥ {formatCount(film.like_count)}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
