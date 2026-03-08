import Link from 'next/link';

interface SectionHeaderProps {
  title: string;
  seeAllHref?: string;
}

export default function SectionHeader({ title, seeAllHref }: SectionHeaderProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
      <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#e0e0ff' }}>{title}</h2>
      {seeAllHref && (
        <Link href={seeAllHref} style={{ fontSize: '14px', color: '#9b8fff', textDecoration: 'none' }}>
          See all →
        </Link>
      )}
    </div>
  );
}
