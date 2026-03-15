import { NextRequest, NextResponse } from 'next/server';
import { timelinesStore } from '../../../../../lib/store';

export async function POST(
  req: NextRequest,
  { params }: { params: { projectId: string } }
) {
  const body = await req.json();
  const { clip_ids } = body as { clip_ids?: string[] };
  if (!Array.isArray(clip_ids)) {
    return NextResponse.json(
      { error: 'clip_ids array is required' },
      { status: 400 }
    );
  }
  try {
    const updated = timelinesStore.reorderClips(params.projectId, clip_ids);
    if (!updated) {
      return NextResponse.json(
        { error: 'Timeline not found' },
        { status: 404 }
      );
    }
    return NextResponse.json(updated);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Reorder failed';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
