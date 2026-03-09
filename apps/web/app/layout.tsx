import './globals.css';

export const metadata = {
  title: 'CineForge',
  description: 'An application for film enthusiasts',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}