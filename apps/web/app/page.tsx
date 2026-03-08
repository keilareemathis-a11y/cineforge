import { getHomepageData } from '../lib/api/platform';
import FilmCard from '../components/platform/FilmCard';
import CreatorCard from '../components/platform/CreatorCard';
import SectionHeader from '../components/platform/SectionHeader';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  const { trending, newReleases, popularCreators } = await getHomepageData();

  return (
    <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '40px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 800, color: '#e0e0ff' }}>🎬 CineForge</h1>
          <p style={{ margin: '4px 0 0', color: '#888', fontSize: '14px' }}>AI-powered short films by independent creators</p>
        </div>
        <Link href="/films/new/editor" style={{ background: '#7c6fff', color: '#fff', padding: '10px 20px', borderRadius: '8px', textDecoration: 'none', fontWeight: 600, fontSize: '14px' }}>
          + Create Film
        </Link>
      </div>

      <section style={{ marginBottom: '40px' }}>
        <SectionHeader title="🔥 Trending" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {trending.map((film) => <FilmCard key={film.id} film={film} />)}
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <SectionHeader title="✨ New Releases" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {newReleases.map((film) => <FilmCard key={film.id} film={film} />)}
        </div>
      </section>

      <section>
        <SectionHeader title="🌟 Popular Creators" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {popularCreators.map((creator) => <CreatorCard key={creator.id} creator={creator} />)}
        </div>
      </section>
    </main>
  );
}