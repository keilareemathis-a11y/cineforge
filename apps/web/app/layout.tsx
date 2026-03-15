import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'CineForge',
  description: 'Create and discover AI-powered short films',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          style={{
            position: 'absolute',
            left: '-9999px',
            top: 'auto',
            width: '1px',
            height: '1px',
            overflow: 'hidden',
          }}
          onFocus={(e) => {
            e.currentTarget.style.left = '8px';
            e.currentTarget.style.top = '8px';
            e.currentTarget.style.width = 'auto';
            e.currentTarget.style.height = 'auto';
          }}
          onBlur={(e) => {
            e.currentTarget.style.left = '-9999px';
            e.currentTarget.style.top = 'auto';
            e.currentTarget.style.width = '1px';
            e.currentTarget.style.height = '1px';
          }}
        >
          Skip to main content
        </a>
        <nav
          aria-label="Main navigation"
          style={{
            background: '#0d0d1e',
            borderBottom: '1px solid #1a1a3a',
            padding: '0 16px',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          <div
            style={{
              maxWidth: '1100px',
              margin: '0 auto',
              display: 'flex',
              alignItems: 'center',
              gap: '24px',
              height: '52px',
            }}
          >
            <Link
              href="/"
              aria-label="CineForge home"
              style={{
                fontSize: '18px',
                fontWeight: 800,
                color: '#e0e0ff',
                textDecoration: 'none',
              }}
            >
              🎬 CineForge
            </Link>
            <Link
              href="/projects"
              style={{
                fontSize: '14px',
                color: '#aaa',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              Studio
            </Link>
            <Link
              href="/"
              style={{
                fontSize: '14px',
                color: '#aaa',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              Discover
            </Link>
          </div>
        </nav>
        <div id="main-content">{children}</div>
      </body>
    </html>
  );
}