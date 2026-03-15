import Link from 'next/link';
import type { Project } from '../../lib/store';

interface ProjectCardProps {
  project: Project;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <article
      style={{
        background: '#16162a',
        border: '1px solid #2a2a4a',
        borderRadius: '12px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <div>
        <h2
          style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: 700,
            color: '#e0e0ff',
          }}
        >
          {project.name}
        </h2>
        {project.description && (
          <p
            style={{
              margin: '6px 0 0',
              fontSize: '13px',
              color: '#888',
              lineHeight: 1.5,
            }}
          >
            {project.description}
          </p>
        )}
        <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#555' }}>
          Created{' '}
          {new Date(project.created_at).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </p>
      </div>

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <Link
          href={`/projects/${project.id}`}
          style={{
            background: '#7c6fff',
            color: '#fff',
            padding: '7px 14px',
            borderRadius: '6px',
            textDecoration: 'none',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          Open
        </Link>
        <Link
          href={`/projects/${project.id}/timeline`}
          style={{
            background: 'transparent',
            color: '#7c6fff',
            padding: '7px 14px',
            borderRadius: '6px',
            textDecoration: 'none',
            fontSize: '13px',
            fontWeight: 600,
            border: '1px solid #7c6fff',
          }}
        >
          Timeline
        </Link>
      </div>
    </article>
  );
}
