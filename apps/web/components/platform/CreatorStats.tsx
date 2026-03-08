import type { CreatorProfile } from '../../types/platform';

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

interface CreatorStatsProps {
  creator: CreatorProfile;
}

export default function CreatorStats({ creator }: CreatorStatsProps) {
  const stats = [
    { label: 'Followers', value: formatCount(creator.follower_count) },
    { label: 'Total Views', value: formatCount(creator.total_views) },
    { label: 'Films', value: String(creator.film_count) },
  ];

  return (
    <div style={{ display: 'flex', gap: '24px', padding: '16px 24px', background: '#1a1a2e', borderRadius: '8px', marginBottom: '24px' }}>
      {stats.map((s) => (
        <div key={s.label} style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '22px', fontWeight: 700, color: '#e0e0ff' }}>{s.value}</div>
          <div style={{ fontSize: '12px', color: '#888' }}>{s.label}</div>
        </div>
      ))}
    </div>
  );
}
