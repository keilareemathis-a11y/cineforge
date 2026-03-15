import { NextRequest, NextResponse } from 'next/server';
import { projectsStore } from '../../../lib/store';

export async function GET() {
  const projects = projectsStore.list();
  return NextResponse.json(projects);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { name, description } = body as { name?: string; description?: string };
  if (!name || name.trim() === '') {
    return NextResponse.json({ error: 'name is required' }, { status: 400 });
  }
  const project = projectsStore.create({ name: name.trim(), description });
  return NextResponse.json(project, { status: 201 });
}
