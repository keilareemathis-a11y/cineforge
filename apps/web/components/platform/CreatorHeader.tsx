import Image from 'next/image';
import Link from 'next/link';
import type { CreatorProfile } from '../../types/platform';

interface CreatorHeaderProps {
  creator: CreatorProfile;
}

export default function CreatorHeader({ creator }: CreatorHeaderProps) {
  return (
    <div>
      <div style={{ position: 'relative', width: '100%', height: '200px', background: '#0f0f1e', borderRadius: '8px', overflow: 'hidden', marginBottom: '-40px' }}>
        <Image src={creator.banner_url} alt="Banner" fill style={{ objectFit: 'cover' }} />
      </div>
      <div style={{ padding: '0 24px 16px', display: 'flex', alignItems: 'flex-end', gap: '16px' }}>
        <div style={{ position: 'relative', width: 80, height: 80, flexShrink: 0, borderRadius: '50%', overflow: 'hidden', border: '3px solid #0d0d1e', background: '#1a1a2e' }}>
          <Image src={creator.avatar_url} alt={creator.display_name} fill style={{ objectFit: 'cover' }} />
        </div>
        <div style={{ paddingBottom: '8px' }}>
          <h1 style={{ margin: '0 0 2px', fontSize: '22px', color: '#e0e0ff' }}>{creator.display_name}</h1>
          <div style={{ color: '#9b8fff', fontSize: '14px' }}>@{creator.handle}</div>
        </div>
      </div>
      <div style={{ padding: '0 24px 16px' }}>
        <p style={{ color: '#ccc', fontSize: '15px', marginBottom: '12px' }}>{creator.bio}</p>
        <Link href={`/films/new/editor`} style={{ display: 'inline-block', background: '#7c6fff', color: '#fff', padding: '8px 18px', borderRadius: '6px', textDecoration: 'none', fontSize: '14px' }}>
          + Create Film
        </Link>
      </div>
    </div>
  );
}
