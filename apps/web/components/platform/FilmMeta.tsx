'use client';
import { useState } from 'react';
import Link from 'next/link';
import type { PublishedFilm } from '../../types/platform';
import { likeFilm } from '../../lib/api/platform';

interface FilmMetaProps {
  film: PublishedFilm;
}

export default function FilmMeta({ film }: FilmMetaProps) {
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(film.like_count);

  const handleLike = async () => {
    if (liked) return;
    setLiked(true);
    setLikeCount((c) => c + 1);
    await likeFilm(film.id);
  };

  return (
    <div style={{ padding: '20px 0' }}>
      <h1 style={{ margin: '0 0 8px', fontSize: '24px', color: '#e0e0ff' }}>{film.title}</h1>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{ color: '#aaa', fontSize: '14px' }}>by</span>
        <Link href={`/creator/${film.creator.handle}`} style={{ color: '#9b8fff', textDecoration: 'none', fontWeight: 600 }}>
          {film.creator.display_name}
        </Link>
        <span style={{ color: '#555' }}>·</span>
        <span style={{ color: '#888', fontSize: '13px' }}>{new Date(film.published_at).toLocaleDateString()}</span>
      </div>
      <p style={{ color: '#ccc', fontSize: '15px', lineHeight: 1.6, marginBottom: '16px' }}>{film.description}</p>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handleLike}
          style={{
            background: liked ? '#7c6fff' : '#2a2a4e',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 18px',
            cursor: liked ? 'default' : 'pointer',
            fontSize: '14px',
          }}
        >
          {liked ? '♥ Liked' : `♥ Like (${likeCount})`}
        </button>
        <button
          onClick={() => navigator.clipboard?.writeText(window.location.href)}
          style={{
            background: '#2a2a4e',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 18px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Share
        </button>
      </div>
      <div style={{ display: 'flex', gap: '16px', marginTop: '12px', fontSize: '13px', color: '#888' }}>
        <span>👁 {film.view_count.toLocaleString()} views</span>
        <span>{film.tags.map((t) => `#${t}`).join(' ')}</span>
      </div>
    </div>
  );
}
