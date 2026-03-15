import { NextRequest, NextResponse } from 'next/server';
import { timelinesStore, shotsStore, versionsStore, projectsStore } from '../../../../lib/store';

export async function POST(
  _req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const project = projectsStore.get(params.projectId);
  if (!project) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }

  const timeline = timelinesStore.getByProject(params.projectId);
  const clips = timeline?.clips ?? [];

  // Build a manifest of what would be exported (stub – no actual rendering)
  const manifest = clips.map((clip) => {
    const shot = shotsStore.get(clip.shot_id);
    const version = clip.version_id
      ? versionsStore.get(clip.version_id)
      : null;
    return {
      clip_id: clip.id,
      position: clip.position,
      duration: clip.duration,
      shot_title: shot?.title ?? 'Unknown shot',
      shot_prompt: shot?.prompt ?? '',
      image_url: version?.image_url ?? null,
    };
  });

  return NextResponse.json({
    status: 'queued',
    message: 'Export job queued (stub). Full rendering is not yet implemented.',
    project_id: params.projectId,
    project_name: project.name,
    clip_count: clips.length,
    total_duration_seconds: clips.reduce((sum, c) => sum + c.duration, 0),
    manifest,
    export_url: null,
  });
}
