// Pyodide loader.
//
// This module owns the expensive, once-per-page work:
//   1. download the WebAssembly Python runtime,
//   2. attach it to the <canvas id="canvas"> element (must happen BEFORE pygame
//      is imported),
//   3. download the pygame-ce wheel,
//   4. copy our .py files into the in-memory filesystem,
//   5. drive one Python frame per browser animation frame.
//
// Everything above the `boot()` call is plain static hosting: the runtime and
// the wheel come from jsDelivr, our own files are a handful of kilobytes.

const PYODIDE_VERSION = "314.0.8"; // keep in sync with docs/ARCHITECTURE.md
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const FS_ROOT = "/app";
const BOOT_TIMEOUT_MS = 180_000;

// Site assets are shared by the home page and by /snake/ and /tic-tac-toe/.
// Resolving against this module (src/loader.js) rather than the current page
// keeps manifest.json and python/ working from every URL depth.
const SITE_ROOT = new URL("../", import.meta.url);

function siteAsset(path) {
  return new URL(path, SITE_ROOT).href;
}

let pyodide = null;
let api = null;
let bootPromise = null;
let rafId = 0;
let lastFrameMs = 0;

/** True once pygame is initialized and Python frames can be requested. */
export function isBooted() {
  return api !== null;
}

/**
 * Download and prepare the runtime. Safe to call twice: concurrent and repeat
 * callers share the same promise, and a failed boot can be retried.
 *
 * @param {(text: string, fraction: number) => void} [onProgress]
 */
export async function boot({ onProgress } = {}) {
  if (api) return api;
  if (bootPromise) return bootPromise;

  bootPromise = (async () => {
    onProgress?.("Loading the game…", 0.04);

    const { loadPyodide } = await import(`${PYODIDE_BASE}pyodide.mjs`);
    pyodide = await loadPyodide({ indexURL: PYODIDE_BASE });

    // Required for SDL-based packages on recent Pyodide builds. Undocumented,
    // hence the guard: if the private hook disappears the games still work.
    try {
      pyodide._api._skip_unwind_fatal_error = true;
    } catch {
      /* ignore */
    }

    // SDL can only ever target one canvas, and the element must exist first.
    // This call MUST run before the `pygame` module is imported.
    const canvas = document.getElementById("canvas");
    if (!canvas) throw new Error('Missing <canvas id="canvas"> element.');
    pyodide.canvas.setCanvas2D(canvas);

    onProgress?.("Almost there…", 0.32);
    await pyodide.loadPackage("pygame-ce");

    await loadProgram(onProgress);
    onProgress?.("Starting the game…", 0.96);

    api = pyodide.pyimport("boot");
    console.info("[loader] Python module ready");
    onProgress?.("Ready", 1);
    return api;
  })();

  try {
    return await withTimeout(
      bootPromise,
      BOOT_TIMEOUT_MS,
      "The Python runtime did not finish booting. Check your connection and reload.",
    );
  } catch (error) {
    bootPromise = null;
    api = null;
    throw error;
  }
}

function withTimeout(promise, ms, message) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(message)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

/** Fetch every file listed in manifest.json into the Pyodide memory filesystem. */
async function loadProgram(onProgress) {
  const manifest = await fetchJson(`${siteAsset("manifest.json")}?t=${Date.now()}`);
  const files = Array.isArray(manifest.files) ? manifest.files : [];
  const version = encodeURIComponent(manifest.version ?? "1");

  let done = 0;
  await Promise.all(
    files.map(async (path) => {
      const response = await fetch(`${siteAsset(path)}?v=${version}`);
      if (!response.ok) {
        throw new Error(`Could not load ${path} (HTTP ${response.status}).`);
      }
      const bytes = new Uint8Array(await response.arrayBuffer());
      const target = `${FS_ROOT}/${path}`;
      mkdirTree(target.slice(0, target.lastIndexOf("/")));
      pyodide.FS.writeFile(target, bytes);

      done += 1;
      onProgress?.(
        "Loading the game…",
        0.5 + 0.42 * (done / files.length),
      );
    }),
  );

  pyodide.runPython(
    `import sys\nsys.path.insert(0, ${JSON.stringify(`${FS_ROOT}/python`)})`,
  );
  return files.length;
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${url} (HTTP ${response.status}).`);
  return response.json();
}

function mkdirTree(path) {
  let current = "";
  for (const part of path.split("/").filter(Boolean)) {
    current += `/${part}`;
    try {
      pyodide.FS.mkdir(current);
    } catch {
      /* already exists */
    }
  }
}

/** Show a game. Python keeps the runtime alive and swaps a scene object. */
export function switchGame(slug) {
  if (!api) throw new Error("switchGame() called before boot().");
  api.switch_game(slug);
}

/** Queue a keyboard/touch action for the running scene. */
export function press(action) {
  if (!api) return;
  api.press(action);
}

/** Queue a canvas tap in logical 720x720 coordinates. */
export function pointerDown(x, y) {
  if (!api) return;
  api.pointer_down(x, y);
}

/**
 * Drive Python from requestAnimationFrame instead of an asyncio loop.
 *
 * One JS callback per frame means Python can never block the tab, pausing is
 * just cancelAnimationFrame(), and a Python exception can be caught and shown
 * instead of freezing the canvas.
 */
export function startLoop(onError) {
  if (!api || rafId) return;

  const tick = (nowMs) => {
    if (!lastFrameMs) lastFrameMs = nowMs;
    const dt = Math.min((nowMs - lastFrameMs) / 1000, 0.05); // clamp tab-switch spikes
    lastFrameMs = nowMs;

    try {
      api.arcade_frame(dt);
    } catch (error) {
      stopLoop();
      onError?.(error);
      return;
    }
    rafId = window.requestAnimationFrame(tick);
  };

  rafId = window.requestAnimationFrame(tick);
}

/** Stop requesting frames. The Python runtime stays loaded for instant resumes. */
export function stopLoop() {
  if (rafId) window.cancelAnimationFrame(rafId);
  rafId = 0;
  lastFrameMs = 0;
}
