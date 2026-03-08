import { getFilmById, getHomepageData } from '../../../lib/api/platform';
import FilmPlayer from '../../../components/platform/FilmPlayer';
import FilmMeta from '../../../components/platform/FilmMeta';
import SupportCreatorPanel from '../../../components/platform/SupportCreatorPanel';
import FilmCard from '../../../components/platform/FilmCard';
import SectionHeader from '../../../components/platform/SectionHeader';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

interface Props {
  params: { filmId: string };
}

export default async function FilmPage({ params }: Props) {
  let film;
  try {
    film = await getFilmById(params.filmId);
  } catch {
    return (
      <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 16px', textAlign: 'center' }}>
        <h1 style={{ color: '#f55' }}>Film not found</h1>
        <Link href="/" style={{ color: '#9b8fff' }}>← Back to home</Link>
      </main>
    );
  }

  const { trending } = await getHomepageData();
  const related = trending.filter((f) => f.id !== film.id).slice(0, 3);

  return (
    <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 16px' }}>
      <Link href="/" style={{ color: '#9b8fff', textDecoration: 'none', fontSize: '14px' }}>← Back to home</Link>
      <div style={{ marginTop: '16px' }}>
        <FilmPlayer film={film} />
        <FilmMeta film={film} />
        <SupportCreatorPanel creator={film.creator} />
      </div>

      {related.length > 0 && (
        <section style={{ marginTop: '40px' }}>
          <SectionHeader title="More Films" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' }}>
            {related.map((f) => <FilmCard key={f.id} film={f} />)}
          </div>
        </section>
      )}
    </main>
  );
}
