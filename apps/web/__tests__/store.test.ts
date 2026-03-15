/**
 * Smoke tests for the CineForge Next.js JSON data store.
 *
 * These tests exercise the store functions directly (no HTTP server needed).
 * A fresh temporary directory is used so tests don't affect real data.
 */

import os from 'os';
import path from 'path';
import fs from 'fs';

// Create a dedicated temp directory for this test run and direct the store
// to it via the CINEFORGE_DATA_DIR env var BEFORE importing the store module.
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cineforge-test-'));
process.env.CINEFORGE_DATA_DIR = tmpDir;

afterAll(() => {
  delete process.env.CINEFORGE_DATA_DIR;
  fs.rmSync(tmpDir, { recursive: true, force: true });
});

// Import store after setting the env override
import {
  projectsStore,
  shotsStore,
  versionsStore,
  timelinesStore,
} from '../lib/store';

// ─── Projects ─────────────────────────────────────────────────────────────────

describe('projectsStore', () => {
  let projectId: string;

  test('list() returns empty array initially', () => {
    expect(projectsStore.list()).toEqual([]);
  });

  test('create() adds a project and returns it', () => {
    const p = projectsStore.create({ name: 'Test Film', description: 'A test' });
    projectId = p.id;
    expect(p.id).toBeTruthy();
    expect(p.name).toBe('Test Film');
    expect(p.description).toBe('A test');
    expect(typeof p.created_at).toBe('string');
  });

  test('list() returns created project', () => {
    const list = projectsStore.list();
    expect(list.length).toBe(1);
    expect(list[0].id).toBe(projectId);
  });

  test('get() returns the project', () => {
    const p = projectsStore.get(projectId);
    expect(p).toBeDefined();
    expect(p!.name).toBe('Test Film');
  });

  test('get() returns undefined for unknown id', () => {
    expect(projectsStore.get('nonexistent')).toBeUndefined();
  });

  test('update() modifies a project', () => {
    const updated = projectsStore.update(projectId, { name: 'Updated Film' });
    expect(updated).toBeDefined();
    expect(updated!.name).toBe('Updated Film');
  });

  test('update() returns null for unknown id', () => {
    expect(projectsStore.update('nonexistent', { name: 'X' })).toBeNull();
  });
});

// ─── Shots ────────────────────────────────────────────────────────────────────

describe('shotsStore', () => {
  let projectId: string;
  let shotId: string;

  beforeAll(() => {
    const p = projectsStore.create({ name: 'Shot Project' });
    projectId = p.id;
  });

  test('list() returns empty for a new project', () => {
    expect(shotsStore.list(projectId)).toEqual([]);
  });

  test('create() adds a shot', () => {
    const s = shotsStore.create({
      project_id: projectId,
      title: 'Opening shot',
      prompt: 'Wide angle cityscape at dusk',
    });
    shotId = s.id;
    expect(s.id).toBeTruthy();
    expect(s.project_id).toBe(projectId);
    expect(s.title).toBe('Opening shot');
    expect(s.active_version_id).toBeNull();
  });

  test('list(projectId) returns shot', () => {
    const shots = shotsStore.list(projectId);
    expect(shots.length).toBe(1);
    expect(shots[0].id).toBe(shotId);
  });

  test('get() returns the shot', () => {
    const s = shotsStore.get(shotId);
    expect(s).toBeDefined();
    expect(s!.title).toBe('Opening shot');
  });

  test('update() changes shot fields', () => {
    const updated = shotsStore.update(shotId, { title: 'New title' });
    expect(updated!.title).toBe('New title');
  });

  test('delete() removes a shot', () => {
    const tmpShot = shotsStore.create({
      project_id: projectId,
      title: 'Temp',
      prompt: 'Temp',
    });
    expect(shotsStore.delete(tmpShot.id)).toBe(true);
    expect(shotsStore.get(tmpShot.id)).toBeUndefined();
  });
});

// ─── ShotVersions ─────────────────────────────────────────────────────────────

describe('versionsStore', () => {
  let projectId: string;
  let shotId: string;
  let versionId: string;

  beforeAll(() => {
    const p = projectsStore.create({ name: 'Versions Project' });
    projectId = p.id;
    const s = shotsStore.create({
      project_id: projectId,
      title: 'Version shot',
      prompt: 'Neon streets at night',
    });
    shotId = s.id;
  });

  test('list() returns empty initially', () => {
    expect(versionsStore.list(shotId)).toEqual([]);
  });

  test('create() adds a version and sets it as active', () => {
    const v = versionsStore.create({
      shot_id: shotId,
      prompt: 'Neon streets at night',
      image_url: 'https://example.com/image.png',
      provider: 'openai',
    });
    versionId = v.id;
    expect(v.version_number).toBe(1);
    expect(v.status).toBe('ready');
    expect(v.image_url).toBe('https://example.com/image.png');

    // The shot should now have this version as active
    const shot = shotsStore.get(shotId);
    expect(shot!.active_version_id).toBe(versionId);
  });

  test('create() increments version_number', () => {
    const v2 = versionsStore.create({
      shot_id: shotId,
      prompt: 'Neon streets at night v2',
      image_url: 'https://example.com/image2.png',
    });
    expect(v2.version_number).toBe(2);
    versionId = v2.id; // now v2 is active
  });

  test('list() returns versions in descending order', () => {
    const versions = versionsStore.list(shotId);
    expect(versions.length).toBe(2);
    expect(versions[0].version_number).toBe(2);
    expect(versions[1].version_number).toBe(1);
  });

  test('get() retrieves a version by id', () => {
    const v = versionsStore.get(versionId);
    expect(v).toBeDefined();
  });

  test('selecting a version updates shot.active_version_id', () => {
    const allVersions = versionsStore.list(shotId);
    const v1Id = allVersions.find((v) => v.version_number === 1)!.id;
    shotsStore.update(shotId, { active_version_id: v1Id });
    expect(shotsStore.get(shotId)!.active_version_id).toBe(v1Id);
  });
});

// ─── Timelines ────────────────────────────────────────────────────────────────

describe('timelinesStore', () => {
  let projectId: string;
  let shotId: string;
  let versionId: string;

  beforeAll(() => {
    const p = projectsStore.create({ name: 'Timeline Project' });
    projectId = p.id;
    const s = shotsStore.create({
      project_id: projectId,
      title: 'TL Shot',
      prompt: 'A dramatic reveal',
    });
    shotId = s.id;
    const v = versionsStore.create({
      shot_id: shotId,
      prompt: 'A dramatic reveal',
      image_url: null,
    });
    versionId = v.id;
  });

  test('getByProject() returns null when no timeline exists', () => {
    expect(timelinesStore.getByProject(projectId)).toBeNull();
  });

  test('getOrCreate() creates a timeline', () => {
    const tl = timelinesStore.getOrCreate(projectId);
    expect(tl.project_id).toBe(projectId);
    expect(tl.clips).toEqual([]);
  });

  test('addClip() adds a clip to the timeline', () => {
    const tl = timelinesStore.addClip(projectId, {
      shot_id: shotId,
      version_id: versionId,
      duration: 4,
    });
    expect(tl.clips.length).toBe(1);
    expect(tl.clips[0].shot_id).toBe(shotId);
    expect(tl.clips[0].duration).toBe(4);
  });

  test('addClip() adds a second clip', () => {
    const s2 = shotsStore.create({
      project_id: projectId,
      title: 'Second shot',
      prompt: 'Second scene',
    });
    const tl = timelinesStore.addClip(projectId, {
      shot_id: s2.id,
      version_id: null,
      duration: 6,
    });
    expect(tl.clips.length).toBe(2);
  });

  test('reorderClips() changes clip order', () => {
    const before = timelinesStore.getByProject(projectId)!;
    const [first, second] = before.clips;
    const tl = timelinesStore.reorderClips(projectId, [second.id, first.id]);
    expect(tl!.clips[0].id).toBe(second.id);
    expect(tl!.clips[0].position).toBe(0);
    expect(tl!.clips[1].id).toBe(first.id);
    expect(tl!.clips[1].position).toBe(1);
  });

  test('removeClip() removes a clip and re-indexes positions', () => {
    const before = timelinesStore.getByProject(projectId)!;
    const clipToRemove = before.clips[0];
    const tl = timelinesStore.removeClip(projectId, clipToRemove.id);
    expect(tl!.clips.length).toBe(1);
    expect(tl!.clips[0].position).toBe(0);
  });

  test('projectsStore.delete() cascades to shots, versions, and timelines', () => {
    // verify data exists
    expect(shotsStore.get(shotId)).toBeDefined();
    expect(timelinesStore.getByProject(projectId)).toBeDefined();

    const deleted = projectsStore.delete(projectId);
    expect(deleted).toBe(true);

    expect(projectsStore.get(projectId)).toBeUndefined();
    expect(shotsStore.list(projectId)).toEqual([]);
    expect(timelinesStore.getByProject(projectId)).toBeNull();
  });
});
