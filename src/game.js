// One game per page: boot the runtime, switch to this page's game, run frames.
//
// Every game page declares its slug on <body data-game="...">. Because these are
// real pages, the browser's own history and the "All games" link handle
// navigation — there is no router to keep in sync.

import { boot, isBooted, press, startLoop, stopLoop, switchGame } from "./loader.js";
import { disableControls, enableControls } from "./controls.js";

const slug = document.body.dataset.game;
const pageTitle = document.title;
const canvas = document.getElementById("canvas");
const bootOverlay = document.getElementById("boot-overlay");
const bootStatus = document.getElementById("boot-status");
const bootBar = document.getElementById("boot-bar");
const errorOverlay = document.getElementById("error-overlay");
const errorText = document.getElementById("error-text");

function setProgress(text, fraction) {
  bootStatus.textContent = text;
  bootBar.style.width = `${Math.max(0, Math.min(1, fraction ?? 0)) * 100}%`;
}

function showError(error) {
  console.error(error);
  const text = error?.message ? String(error.message) : String(error);
  errorText.textContent = text.slice(0, 4000);
  bootOverlay.hidden = true;
  errorOverlay.hidden = false;
}

function goHome() {
  window.location.assign("../");
}

async function start() {
  enableControls((action) => {
    if (action === "escape") {
      goHome();
    } else {
      press(action);
    }
  });

  try {
    if (!isBooted()) {
      await boot({ onProgress: setProgress });
    }

    switchGame(slug);
    bootOverlay.hidden = true;
    // pygame's SDL layer renames the browser tab to its window caption on
    // startup; put the page's own title back.
    document.title = pageTitle;
    startLoop(showError);
    canvas.focus({ preventScroll: true });
  } catch (error) {
    showError(error);
  }
}

// Leaving the page frees the frame loop and keyboard listener immediately.
window.addEventListener("pagehide", () => {
  stopLoop();
  disableControls();
});

start();
