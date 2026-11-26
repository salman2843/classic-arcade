// Input plumbing: keyboard, canvas taps and on-screen buttons all end up as the
// same string actions ("left", "pause", …) inside Python's InputQueue.

import { pointerDown } from "./loader.js";

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

function onKeyDown(event) {
  if (!send) return;
  const action = KEY_ACTIONS[event.key.toLowerCase()];
  if (!action) return;
  event.preventDefault();
  if (!event.repeat) send(action);
}

/**
 * Enable every input source while a game page is open.
 * @param {(action: string) => void} handler
 */
export function enableControls(handler) {
  send = handler;
  if (listening) return;
  listening = true;
  window.addEventListener("keydown", onKeyDown);
}

/** Detach keyboard handling when the page goes away (listeners would pile up otherwise). */
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
