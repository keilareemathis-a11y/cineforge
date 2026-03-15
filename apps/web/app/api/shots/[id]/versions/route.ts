import { NextRequest, NextResponse } from 'next/server';
import { versionsStore, shotsStore } from '../../../../../lib/store';

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  const shot = shotsStore.get(params.id);
  if (!shot) {
    return NextResponse.json({ error: 'Shot not found' }, { status: 404 });
  }
  const versions = versionsStore.list(params.id);
  return NextResponse.json({
    shot_id: params.id,
    active_version_id: shot.active_version_id,
    versions,
  });
}
