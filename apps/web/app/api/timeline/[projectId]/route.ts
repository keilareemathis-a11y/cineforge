import { NextRequest, NextResponse } from 'next/server';
import { timelinesStore, projectsStore } from '../../../../lib/store';

export async function GET(
  _req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  if (!projectsStore.get(params.projectId)) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  const timeline = timelinesStore.getOrCreate(params.projectId);
  return NextResponse.json(timeline);
}
