import { NextRequest, NextResponse } from 'next/server';
import { timelinesStore, shotsStore, projectsStore } from '../../../../../lib/store';

export async function POST(
  req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  if (!projectsStore.get(params.projectId)) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  const body = await req.json();
  const { shot_id, version_id, duration } = body as {
    shot_id?: string;
    version_id?: string | null;
    duration?: number;
  };
  if (!shot_id) {
    return NextResponse.json({ error: 'shot_id is required' }, { status: 400 });
  }
  const shot = shotsStore.get(shot_id);
  if (!shot || shot.project_id !== params.projectId) {
    return NextResponse.json({ error: 'Shot not found in this project' }, { status: 404 });
  }
  const timeline = timelinesStore.addClip(params.projectId, {
    shot_id,
    version_id: version_id ?? shot.active_version_id ?? null,
    duration: duration ?? 5,
  });
  return NextResponse.json(timeline, { status: 201 });
}
