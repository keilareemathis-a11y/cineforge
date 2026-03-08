'use client';
import Link from 'next/link';
import Image from 'next/image';
import type { CreatorProfile } from '../../types/platform';

function formatCount(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

interface CreatorCardProps {
  creator: CreatorProfile;
}

export default function CreatorCard({ creator }: CreatorCardProps) {
  return (
    <Link href={`/creator/${creator.handle}`} style={{ textDecoration: 'none', color: 'inherit' }}>
      <div style={{
        borderRadius: '8px',
        padding: '16px',
        background: '#1a1a2e',
        border: '1px solid #2a2a4e',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        cursor: 'pointer',
      }}>
        <div style={{ position: 'relative', width: 56, height: 56, flexShrink: 0 }}>
          <Image
            src={creator.avatar_url}
            alt={creator.display_name}
            fill
            style={{ objectFit: 'cover', borderRadius: '50%' }}
          />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, color: '#e0e0ff', fontSize: '15px' }}>{creator.display_name}</div>
          <div style={{ color: '#9b8fff', fontSize: '13px', marginBottom: '4px' }}>@{creator.handle}</div>
          <div style={{ color: '#aaa', fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {creator.bio}
          </div>
          <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '12px', color: '#888' }}>
            <span>{formatCount(creator.follower_count)} followers</span>
            <span>{creator.film_count} films</span>
          </div>
        </div>
        <button
          onClick={(e) => e.preventDefault()}
          style={{
            background: '#7c6fff',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '13px',
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          Follow
        </button>
      </div>
    </Link>
  );
}
