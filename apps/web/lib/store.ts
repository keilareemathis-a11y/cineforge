import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';

const DATA_DIR =
  process.env.CINEFORGE_DATA_DIR ?? path.join(process.cwd(), 'data');
const DB_FILE = path.join(DATA_DIR, 'db.json');

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Shot {
  id: string;
  project_id: string;
  title: string;
  prompt: string;
  active_version_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShotVersion {
  id: string;
  shot_id: string;
  version_number: number;
  prompt: string;
  image_url: string | null;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  provider: string;
  created_at: string;
}

export interface Clip {
  id: string;
  shot_id: string;
  version_id: string | null;
  position: number;
  duration: number;
}

export interface Timeline {
  id: string;
  project_id: string;
  clips: Clip[];
  created_at: string;
  updated_at: string;
}

interface Db {
  projects: Project[];
  shots: Shot[];
  shot_versions: ShotVersion[];
  timelines: Timeline[];
}

function ensureDataDir(): void {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
}

function readDb(): Db {
  ensureDataDir();
  if (!fs.existsSync(DB_FILE)) {
    return { projects: [], shots: [], shot_versions: [], timelines: [] };
  }
  try {
    return JSON.parse(fs.readFileSync(DB_FILE, 'utf-8')) as Db;
  } catch {
    return { projects: [], shots: [], shot_versions: [], timelines: [] };
  }
}

function writeDb(db: Db): void {
  ensureDataDir();
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

export function generateId(): string {
  return randomUUID();
}

export const projectsStore = {
  list: (): Project[] => readDb().projects,

  get: (id: string): Project | undefined =>
    readDb().projects.find((p) => p.id === id),

  create: (data: { name: string; description?: string }): Project => {
    const db = readDb();
    const now = new Date().toISOString();
    const project: Project = {
      id: generateId(),
      name: data.name,
      description: data.description ?? '',
      created_at: now,
      updated_at: now,
    };
    db.projects.push(project);
    writeDb(db);
    return project;
  },

  update: (
    id: string,
    data: Partial<Pick<Project, 'name' | 'description'>>
  ): Project | null => {
    const db = readDb();
    const idx = db.projects.findIndex((p) => p.id === id);
    if (idx === -1) return null;
    db.projects[idx] = {
      ...db.projects[idx],
      ...data,
      updated_at: new Date().toISOString(),
    };
    writeDb(db);
    return db.projects[idx];
  },

  delete: (id: string): boolean => {
    const db = readDb();
    const idx = db.projects.findIndex((p) => p.id === id);
    if (idx === -1) return false;
    db.projects.splice(idx, 1);
    const shotIds = db.shots
      .filter((s) => s.project_id === id)
      .map((s) => s.id);
    db.shots = db.shots.filter((s) => s.project_id !== id);
    db.shot_versions = db.shot_versions.filter(
      (v) => !shotIds.includes(v.shot_id)
    );
    db.timelines = db.timelines.filter((t) => t.project_id !== id);
    writeDb(db);
    return true;
  },
};

export const shotsStore = {
  list: (projectId?: string): Shot[] => {
    const shots = readDb().shots;
    return projectId ? shots.filter((s) => s.project_id === projectId) : shots;
  },

  get: (id: string): Shot | undefined =>
    readDb().shots.find((s) => s.id === id),

  create: (data: {
    project_id: string;
    title: string;
    prompt: string;
  }): Shot => {
    const db = readDb();
    const now = new Date().toISOString();
    const shot: Shot = {
      id: generateId(),
      project_id: data.project_id,
      title: data.title,
      prompt: data.prompt,
      active_version_id: null,
      created_at: now,
      updated_at: now,
    };
    db.shots.push(shot);
    writeDb(db);
    return shot;
  },

  update: (
    id: string,
    data: Partial<Pick<Shot, 'title' | 'prompt' | 'active_version_id'>>
  ): Shot | null => {
    const db = readDb();
    const idx = db.shots.findIndex((s) => s.id === id);
    if (idx === -1) return null;
    db.shots[idx] = {
      ...db.shots[idx],
      ...data,
      updated_at: new Date().toISOString(),
    };
    writeDb(db);
    return db.shots[idx];
  },

  delete: (id: string): boolean => {
    const db = readDb();
    const idx = db.shots.findIndex((s) => s.id === id);
    if (idx === -1) return false;
    db.shots.splice(idx, 1);
    db.shot_versions = db.shot_versions.filter((v) => v.shot_id !== id);
    writeDb(db);
    return true;
  },
};

export const versionsStore = {
  list: (shotId: string): ShotVersion[] =>
    readDb()
      .shot_versions.filter((v) => v.shot_id === shotId)
      .sort((a, b) => b.version_number - a.version_number),

  get: (id: string): ShotVersion | undefined =>
    readDb().shot_versions.find((v) => v.id === id),

  create: (data: {
    shot_id: string;
    prompt: string;
    image_url: string | null;
    provider?: string;
  }): ShotVersion => {
    const db = readDb();
    const existing = db.shot_versions.filter(
      (v) => v.shot_id === data.shot_id
    );
    const version: ShotVersion = {
      id: generateId(),
      shot_id: data.shot_id,
      version_number: existing.length + 1,
      prompt: data.prompt,
      image_url: data.image_url,
      status: data.image_url ? 'ready' : 'pending',
      provider: data.provider ?? 'openai',
      created_at: new Date().toISOString(),
    };
    db.shot_versions.push(version);
    const shotIdx = db.shots.findIndex((s) => s.id === data.shot_id);
    if (shotIdx !== -1) {
      db.shots[shotIdx].active_version_id = version.id;
      db.shots[shotIdx].updated_at = new Date().toISOString();
    }
    writeDb(db);
    return version;
  },
};

export const timelinesStore = {
  getByProject: (projectId: string): Timeline | null => {
    const db = readDb();
    return db.timelines.find((t) => t.project_id === projectId) ?? null;
  },

  getOrCreate: (projectId: string): Timeline => {
    const db = readDb();
    const existing = db.timelines.find((t) => t.project_id === projectId);
    if (existing) return existing;
    const now = new Date().toISOString();
    const timeline: Timeline = {
      id: generateId(),
      project_id: projectId,
      clips: [],
      created_at: now,
      updated_at: now,
    };
    db.timelines.push(timeline);
    writeDb(db);
    return timeline;
  },

  addClip: (
    projectId: string,
    data: { shot_id: string; version_id: string | null; duration?: number }
  ): Timeline => {
    const db = readDb();
    let timelineIdx = db.timelines.findIndex(
      (t) => t.project_id === projectId
    );
    if (timelineIdx === -1) {
      const now = new Date().toISOString();
      db.timelines.push({
        id: generateId(),
        project_id: projectId,
        clips: [],
        created_at: now,
        updated_at: now,
      });
      timelineIdx = db.timelines.length - 1;
    }
    const timeline = db.timelines[timelineIdx];
    const clip: Clip = {
      id: generateId(),
      shot_id: data.shot_id,
      version_id: data.version_id,
      position: timeline.clips.length,
      duration: data.duration ?? 5,
    };
    timeline.clips.push(clip);
    timeline.updated_at = new Date().toISOString();
    writeDb(db);
    return db.timelines[timelineIdx];
  },

  reorderClips: (projectId: string, clipIds: string[]): Timeline | null => {
    const db = readDb();
    const idx = db.timelines.findIndex((t) => t.project_id === projectId);
    if (idx === -1) return null;
    const timeline = db.timelines[idx];
    const clipMap = new Map(timeline.clips.map((c) => [c.id, c]));
    timeline.clips = clipIds.map((id, position) => {
      const clip = clipMap.get(id);
      if (!clip) throw new Error(`Clip ID ${id} not found in timeline for project ${projectId}`);
      return { ...clip, position };
    });
    timeline.updated_at = new Date().toISOString();
    writeDb(db);
    return db.timelines[idx];
  },

  removeClip: (projectId: string, clipId: string): Timeline | null => {
    const db = readDb();
    const idx = db.timelines.findIndex((t) => t.project_id === projectId);
    if (idx === -1) return null;
    db.timelines[idx].clips = db.timelines[idx].clips
      .filter((c) => c.id !== clipId)
      .map((c, i) => ({ ...c, position: i }));
    db.timelines[idx].updated_at = new Date().toISOString();
    writeDb(db);
    return db.timelines[idx];
  },
};
