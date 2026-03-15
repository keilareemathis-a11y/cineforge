import { NextRequest, NextResponse } from 'next/server';
import { versionsStore, shotsStore } from '../../../../../../../lib/store';

export async function POST(
  _req: NextRequest,
  { params }: { params: { id: string; versionId: string } }
) {
  const shot = shotsStore.get(params.id);
  if (!shot) {
    return NextResponse.json({ error: 'Shot not found' }, { status: 404 });
  }
  const version = versionsStore.get(params.versionId);
  if (!version || version.shot_id !== params.id) {
    return NextResponse.json({ error: 'Version not found' }, { status: 404 });
  }
  const updated = shotsStore.update(params.id, {
    active_version_id: params.versionId,
  });
  const versions = versionsStore.list(params.id);
  return NextResponse.json({
    shot_id: params.id,
    active_version_id: updated?.active_version_id ?? params.versionId,
    versions,
  });
}
