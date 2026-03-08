'use client';
import { useState } from 'react';
import Image from 'next/image';
import type { PublishedFilm } from '../../types/platform';

interface FilmPlayerProps {
  film: PublishedFilm;
}

export default function FilmPlayer({ film }: FilmPlayerProps) {
  const [playing, setPlaying] = useState(false);

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      paddingTop: '56.25%',
      background: '#0f0f1e',
      borderRadius: '8px',
      overflow: 'hidden',
    }}>
      {film.video_url && playing ? (
        <video
          src={film.video_url}
          autoPlay
          controls
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        <>
          <Image
            src={film.thumbnail_url}
            alt={film.title}
            fill
            style={{ objectFit: 'cover' }}
          />
          <button
            onClick={() => setPlaying(true)}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'rgba(124,111,255,0.9)',
              border: 'none',
              borderRadius: '50%',
              width: '72px',
              height: '72px',
              fontSize: '28px',
              cursor: 'pointer',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ▶
          </button>
        </>
      )}
    </div>
  );
}
