import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { shotsStore, versionsStore } from '../../../../../lib/store';

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const shot = shotsStore.get(params.id);
  if (!shot) {
    return NextResponse.json({ error: 'Shot not found' }, { status: 404 });
  }

  const body = await req.json().catch(() => ({}));
  const prompt: string = (body as { prompt?: string }).prompt ?? shot.prompt;

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    // Return a deterministic placeholder when no key is configured so local
    // dev without a key still works end-to-end.
    const SEED_LENGTH = 20;
    const IMAGE_WIDTH = 640;
    const IMAGE_HEIGHT = 360;
    const placeholder = `https://picsum.photos/seed/${encodeURIComponent(prompt.slice(0, SEED_LENGTH))}/${IMAGE_WIDTH}/${IMAGE_HEIGHT}`;
    const version = versionsStore.create({
      shot_id: params.id,
      prompt,
      image_url: placeholder,
      provider: 'placeholder',
    });
    return NextResponse.json(version, { status: 201 });
  }

  const client = new OpenAI({ apiKey });

  try {
    const response = await client.images.generate({
      model: 'dall-e-3',
      prompt: `Film still: ${prompt}`,
      n: 1,
      size: '1792x1024',
      quality: 'standard',
    });

    const image_url = response.data?.[0]?.url ?? null;
    const version = versionsStore.create({
      shot_id: params.id,
      prompt,
      image_url,
      provider: 'openai',
    });
    return NextResponse.json(version, { status: 201 });
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : 'OpenAI generation failed';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
