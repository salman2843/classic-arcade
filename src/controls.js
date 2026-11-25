// Input plumbing: keyboard, canvas taps and on-screen buttons all end up as the
// same string actions ("left", "pause", …) inside Python's InputQueue.

import { pointerDown, press } from "./loader.js";

const KEY_ACTIONS = {
  arrowleft: "left",
  arrowright: "right",
  arrowup: "up",
  arrowdown: "down",
  a: "left",
  d: "right",
  w: "up",
  s: "down",
  " ": "action",
  enter: "action",
  p: "pause",
  r: "restart",
  escape: "escape",
};

let send = null;
let listening = false;

function normalize(event) {
  return event.key.length === 1 ? event.key.toLowerCase() : event.key.toLowerCase();
}

function onKeyDown(event) {
  if (!send) return;
  const action = KEY_ACTIONS[normalize(event)];
  if (!action) return;
  event.preventDefault();
  if (!event.repeat) send(action);
}

/**
 * Enable every input source while a game is on screen.
 * @param {(action: string) => void} handler
 */
export function enableControls(handler) {
  send = handler;
  if (listening) return;
  listening = true;
  window.addEventListener("keydown", onKeyDown);
}

/** Detach keyboard handling when the stage closes (listeners would pile up otherwise). */
export function disableControls() {
  send = null;
  if (!listening) return;
  listening = false;
  window.removeEventListener("keydown", onKeyDown);
}

/** Convert a pointer position on the scaled canvas into 720x720 game coordinates. */
function canvasPoint(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * canvas.width;
  const y = ((event.clientY - rect.top) / rect.height) * canvas.height;
  return { x, y };
}

// --- canvas taps: tic-tac-toe uses these -------------------------------------

const canvas = document.getElementById("canvas");
if (canvas) {
  canvas.addEventListener("pointerdown", (event) => {
    if (!send) return;
    event.preventDefault();
    canvas.focus({ preventScroll: true });
    const { x, y } = canvasPoint(canvas, event);
    pointerDown(x, y);
  });
}

// --- on-screen D-pad: same actions as the keyboard ---------------------------

for (const button of document.querySelectorAll("[data-action]")) {
  button.addEventListener("pointerdown", (event) => {
    if (!send) return;
    event.preventDefault();
    send(button.dataset.action);
  });
}

// --- audio unlock ------------------------------------------------------------

let audioContext = null;

/**
 * Create/resume an AudioContext during a real click. Browsers block audio that
 * starts without a gesture, so this runs in every Play button handler even
 * though the current games are silent. It is the hook future sound effects use.
 */
export function unlockAudio() {
  try {
    const AudioCtor = window.AudioContext ?? window.webkitAudioContext;
    if (!AudioCtor) return;
    audioContext = audioContext ?? new AudioCtor();
    if (audioContext.state === "suspended") audioContext.resume();
  } catch {
    /* audio is optional */
  }
}

export { press };
