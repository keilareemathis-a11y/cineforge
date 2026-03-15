import { NextRequest, NextResponse } from 'next/server';
import { shotsStore, projectsStore } from '../../../lib/store';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const projectId = searchParams.get('project_id') ?? undefined;
  const shots = shotsStore.list(projectId);
  return NextResponse.json(shots);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { project_id, title, prompt } = body as {
    project_id?: string;
    title?: string;
    prompt?: string;
  };
  if (!project_id || !title || !prompt) {
    return NextResponse.json(
      { error: 'project_id, title, and prompt are required' },
      { status: 400 }
    );
  }
  if (!projectsStore.get(project_id)) {
    return NextResponse.json({ error: 'Project not found' }, { status: 404 });
  }
  const shot = shotsStore.create({
    project_id,
    title: title.trim(),
    prompt: prompt.trim(),
  });
  return NextResponse.json(shot, { status: 201 });
}
