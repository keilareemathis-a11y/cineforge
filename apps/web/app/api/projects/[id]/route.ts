import { NextRequest, NextResponse } from 'next/server';
import { projectsStore } from '../../../../lib/store';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const project = projectsStore.get(params.id);
  if (!project) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  return NextResponse.json(project);
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await req.json();
  const updated = projectsStore.update(params.id, body as { name?: string; description?: string });
  if (!updated) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  return NextResponse.json(updated);
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const deleted = projectsStore.delete(params.id);
  if (!deleted) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  return NextResponse.json({ success: true });
}
