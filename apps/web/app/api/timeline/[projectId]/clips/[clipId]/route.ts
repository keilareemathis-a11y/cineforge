import { NextRequest, NextResponse } from 'next/server';
import { timelinesStore } from '../../../../../../lib/store';

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { projectId: string; clipId: string } }
) {
  const updated = timelinesStore.removeClip(params.projectId, params.clipId);
  if (!updated) {
    return NextResponse.json({ error: 'Timeline not found' }, { status: 404 });
  }
  return NextResponse.json(updated);
}
