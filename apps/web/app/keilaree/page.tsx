'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import Link from 'next/link';

// ── types ─────────────────────────────────────────────────────────────────────

interface Character {
  name: string;
  personality: string;
  trust: number;
  mesh: import('three').Group;
}

interface LogEntry {
  id: number;
  text: string;
}

// ── constants ─────────────────────────────────────────────────────────────────

const PERSONALITIES = ['friendly', 'suspicious', 'curious', 'aggressive', 'calm'];
const LOG_CAP = 100;
let _entryId = 0;

// ── helpers (pure, no DOM) ────────────────────────────────────────────────────

function makeEntry(text: string): LogEntry {
  return { id: _entryId++, text };
}

function randomPersonality(): string {
  return PERSONALITIES[Math.floor(Math.random() * PERSONALITIES.length)];
}

function interactionLine(a: Character, b: Character): string {
  if (a.personality === 'aggressive' || b.personality === 'suspicious') {
    return `⚔️ ${a.name} clashes with ${b.name}!`;
  }
  return `🤝 ${a.name} forms an alliance with ${b.name}.`;
}

function rumorLine(speaker: Character, target: Character): string {
  const rumors = [
    `${speaker.name} whispers that ${target.name} has a secret.`,
    `${speaker.name} tells everyone ${target.name} is planning something.`,
    `${speaker.name} claims ${target.name} can't be trusted.`,
  ];
  return `🗣️ ${rumors[Math.floor(Math.random() * rumors.length)]}`;
}

// ── component ─────────────────────────────────────────────────────────────────

export default function KeilareeStudioPage() {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<import('three').Scene | null>(null);
  const cameraRef = useRef<import('three').PerspectiveCamera | null>(null);
  const rendererRef = useRef<import('three').WebGLRenderer | null>(null);
  const frameRef = useRef<number>(0);
  const worldTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Characters stored outside React state for Three.js mutation
  const charactersRef = useRef<Character[]>([]);

  const [log, setLog] = useState<LogEntry[]>([makeEntry('Welcome to Keilaree AI Story Studio')]);
  const [nameInput, setNameInput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  const logRef = useRef<HTMLOListElement>(null);

  // ── push to log ─────────────────────────────────────────────────────────────

  const pushLog = useCallback((text: string) => {
    setLog((prev) => {
      const next = [...prev, makeEntry(text)];
      return next.length > LOG_CAP ? next.slice(next.length - LOG_CAP) : next;
    });
  }, []);

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log]);

  // ── Three.js scene setup ─────────────────────────────────────────────────────

  useEffect(() => {
    // Dynamic import to avoid SSR issues
    let cancelled = false;

    async function init() {
      const THREE = await import('three');

      if (cancelled || !mountRef.current) return;

      const container = mountRef.current;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;

      // Scene
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x1a1a2e);
      sceneRef.current = scene;

      // Camera
      const camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 1000);
      camera.position.set(0, 10, 14);
      camera.lookAt(0, 0, 0);
      cameraRef.current = camera;

      // Renderer
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);
      rendererRef.current = renderer;

      // Floor
      const floorGeo = new THREE.PlaneGeometry(20, 20);
      const floorMat = new THREE.MeshStandardMaterial({ color: 0x2a2a4e });
      const floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      scene.add(floor);

      // Ambient + directional light
      scene.add(new THREE.AmbientLight(0xffffff, 0.6));
      const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
      dirLight.position.set(5, 10, 5);
      scene.add(dirLight);

      // Initial characters
      const initNames = ['Alice', 'Bob', 'Cara', 'Dev'];
      for (const name of initNames) {
        addCharacterToScene(THREE, scene, name);
      }
      layoutCharacters();

      // Animation loop
      function animate() {
        frameRef.current = requestAnimationFrame(animate);
        renderer.render(scene, camera);
      }
      animate();

      // Resize handler
      function onResize() {
        if (!mountRef.current) return;
        const cw = mountRef.current.clientWidth;
        const ch = mountRef.current.clientHeight;
        camera.aspect = cw / ch;
        camera.updateProjectionMatrix();
        renderer.setSize(cw, ch);
      }
      window.addEventListener('resize', onResize);

      return () => {
        window.removeEventListener('resize', onResize);
      };
    }

    const cleanupPromise = init();

    return () => {
      cancelled = true;
      cleanupPromise.then((cleanup) => {
        cleanup?.();
      });

      // Stop animation
      if (frameRef.current) cancelAnimationFrame(frameRef.current);

      // Clear world timer
      if (worldTimerRef.current) {
        clearInterval(worldTimerRef.current);
        worldTimerRef.current = null;
      }

      // Dispose renderer
      if (rendererRef.current) {
        rendererRef.current.dispose();
        rendererRef.current.domElement.remove();
        rendererRef.current = null;
      }

      // Clear scene
      sceneRef.current = null;
      cameraRef.current = null;
      charactersRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Three.js helpers (need to be defined after state/refs) ──────────────────

  function addCharacterToScene(
    THREE: typeof import('three'),
    scene: import('three').Scene,
    name: string,
  ) {
    const group = new THREE.Group();

    const bodyGeo = new THREE.BoxGeometry(0.8, 1.2, 0.8);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color().setHSL(Math.random(), 0.7, 0.5),
    });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.y = 0.6;
    group.add(body);

    const headGeo = new THREE.SphereGeometry(0.35, 16, 16);
    const headMat = new THREE.MeshStandardMaterial({ color: 0xffe0cc });
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.y = 1.55;
    group.add(head);

    scene.add(group);

    charactersRef.current.push({
      name,
      personality: randomPersonality(),
      trust: Math.random(),
      mesh: group,
    });
  }

  function layoutCharacters() {
    const chars = charactersRef.current;
    const count = chars.length;
    const radius = Math.max(3, count * 0.9);
    chars.forEach((char, i) => {
      const angle = (i / count) * Math.PI * 2;
      char.mesh.position.set(
        Math.cos(angle) * radius,
        0,
        Math.sin(angle) * radius,
      );
    });
  }

  // ── actions ──────────────────────────────────────────────────────────────────

  const doInteraction = useCallback(() => {
    const chars = charactersRef.current;
    if (chars.length < 2) {
      pushLog('⚠️ Need at least 2 characters for an interaction.');
      return;
    }
    const i = Math.floor(Math.random() * chars.length);
    let j = Math.floor(Math.random() * (chars.length - 1));
    if (j >= i) j++;
    pushLog(interactionLine(chars[i], chars[j]));
  }, [pushLog]);

  const doRumor = useCallback(() => {
    const chars = charactersRef.current;
    if (chars.length < 2) {
      pushLog('⚠️ Need at least 2 characters for a rumor.');
      return;
    }
    const i = Math.floor(Math.random() * chars.length);
    let j = Math.floor(Math.random() * (chars.length - 1));
    if (j >= i) j++;
    pushLog(rumorLine(chars[i], chars[j]));
  }, [pushLog]);

  const handleAddCharacter = useCallback(async () => {
    const name = nameInput.trim();
    if (!name) return;

    const THREE = await import('three');
    const scene = sceneRef.current;
    if (!scene) return;

    addCharacterToScene(THREE, scene, name);
    layoutCharacters();

    setNameInput('');
    pushLog(`✨ ${name} joined the story.`);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nameInput, pushLog]);

  const handleRunWorld = useCallback(() => {
    if (worldTimerRef.current) return; // prevent overlapping runs

    setIsRunning(true);
    let step = 0;

    worldTimerRef.current = setInterval(() => {
      step++;
      if (Math.random() < 0.5) doInteraction();
      else doRumor();

      if (step >= 10) {
        clearInterval(worldTimerRef.current!);
        worldTimerRef.current = null;
        setIsRunning(false);
      }
    }, 600);
  }, [doInteraction, doRumor]);

  const handleNameKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') handleAddCharacter();
    },
    [handleAddCharacter],
  );

  // ── render ───────────────────────────────────────────────────────────────────

  return (
    <main style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', background: '#0d0d1e' }}>

      {/* Three.js canvas mount */}
      <div
        ref={mountRef}
        aria-hidden="true"
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
      />

      {/* UI overlay */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          width: 280,
          background: 'rgba(13, 13, 30, 0.92)',
          border: '1px solid #2a2a4e',
          borderRadius: 10,
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          zIndex: 10,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#e0e0ff', letterSpacing: '0.03em' }}>
          Keilaree AI Story Studio
        </h1>

        {/* Add character */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label htmlFor="char-name-input" style={{ fontSize: 12, color: '#9b8fff' }}>
            Character name
          </label>
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              id="char-name-input"
              type="text"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={handleNameKeyDown}
              placeholder="Enter a name…"
              autoComplete="off"
              style={{
                flex: 1,
                background: '#0f0f2e',
                border: '1px solid #3a3a6e',
                borderRadius: 6,
                color: '#e0e0ff',
                fontSize: 13,
                padding: '6px 8px',
                outline: 'none',
              }}
            />
            <button
              type="button"
              onClick={handleAddCharacter}
              style={btnStyle('#7c6fff')}
            >
              Add
            </button>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button type="button" onClick={doInteraction} style={btnStyle('#5a4fcf')}>
            Interaction
          </button>
          <button type="button" onClick={doRumor} style={btnStyle('#5a4fcf')}>
            Rumor
          </button>
          <button
            type="button"
            onClick={handleRunWorld}
            disabled={isRunning}
            aria-disabled={isRunning}
            style={btnStyle(isRunning ? '#3a3a6e' : '#9b3fbf', isRunning)}
          >
            {isRunning ? 'Running…' : 'Run 10 Steps'}
          </button>
        </div>

        {/* Dialogue log */}
        <div>
          <p style={{ margin: '0 0 4px', fontSize: 12, color: '#9b8fff' }}>
            Story log
          </p>
          {/* eslint-disable-next-line jsx-a11y/no-redundant-roles */}
          <ol
            ref={logRef}
            role="log"
            aria-live="polite"
            aria-label="Story dialogue log"
            aria-relevant="additions"
            style={{
              margin: 0,
              padding: '8px 8px 8px 10px',
              background: '#0f0f2e',
              border: '1px solid #2a2a4e',
              borderRadius: 6,
              maxHeight: 220,
              overflowY: 'auto',
              fontSize: 12,
              color: '#ccc',
              listStyle: 'none',
            }}
          >
            {log.map((entry) => (
              <li key={entry.id} style={{ marginBottom: 4, lineHeight: 1.4 }}>
                {entry.text}
              </li>
            ))}
          </ol>
        </div>

        {/* Back link */}
        <Link
          href="/"
          style={{ fontSize: 12, color: '#9b8fff', textDecoration: 'none', marginTop: 2 }}
        >
          ← Back to CineForge
        </Link>
      </div>
    </main>
  );
}

// ── style helper ──────────────────────────────────────────────────────────────

function btnStyle(bg: string, disabled = false): React.CSSProperties {
  return {
    background: bg,
    color: disabled ? '#888' : '#fff',
    border: 'none',
    borderRadius: 6,
    padding: '8px 10px',
    fontSize: 13,
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    width: '100%',
    textAlign: 'left',
    outline: 'none',
  };
}
