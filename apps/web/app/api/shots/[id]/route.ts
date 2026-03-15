import { NextRequest, NextResponse } from 'next/server';
import { shotsStore } from '../../../../lib/store';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const shot = shotsStore.get(params.id);
  if (!shot) {
    return NextResponse.json({ error: 'Shot not found' }, { status: 404 });
  }
  return NextResponse.json(shot);
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await req.json();
  const updated = shotsStore.update(
    params.id,
    body as { title?: string; prompt?: string; active_version_id?: string }
  );
  if (!updated) {
    return NextResponse.json({ error: 'Shot not found' }, { status: 404 });
  }
  return NextResponse.json(updated);
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const deleted = shotsStore.delete(params.id);
  if (!deleted) {
    return NextResponse.json({ error: 'Shot not found' }, { status: 404 });
  }
  return NextResponse.json({ success: true });
}
