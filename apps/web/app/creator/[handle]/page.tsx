import { getCreatorProfile } from '../../../lib/api/platform';
import CreatorHeader from '../../../components/platform/CreatorHeader';
import CreatorStats from '../../../components/platform/CreatorStats';
import FilmCard from '../../../components/platform/FilmCard';
import SectionHeader from '../../../components/platform/SectionHeader';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

interface Props {
  params: { handle: string };
}

export default async function CreatorPage({ params }: Props) {
  let creator;
  try {
    creator = await getCreatorProfile(params.handle);
  } catch {
    return (
      <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 16px', textAlign: 'center' }}>
        <h1 style={{ color: '#f55' }}>Creator not found</h1>
        <Link href="/" style={{ color: '#9b8fff' }}>← Back to home</Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 16px' }}>
      <Link href="/" style={{ color: '#9b8fff', textDecoration: 'none', fontSize: '14px' }}>← Back to home</Link>
      <div style={{ marginTop: '16px' }}>
        <CreatorHeader creator={creator} />
        <CreatorStats creator={creator} />
        {creator.films && creator.films.length > 0 && (
          <section>
            <SectionHeader title="Films" />
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' }}>
              {creator.films.map((film) => <FilmCard key={film.id} film={film} />)}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
