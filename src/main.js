// Page shell: cards, stage visibility, boot progress and the game lifecycle.

import { boot, isBooted, press, startLoop, stopLoop, switchGame } from "./loader.js";
import { disableControls, enableControls, unlockAudio } from "./controls.js";
import { currentSlug, writeSlug } from "./router.js";

const GAMES = {
  tictactoe: {
    title: "Tic-Tac-Toe",
    hint: "You are X. The AI plays O and searches every reply — a draw is a good result.",
    keys: [
      ["Click", "place X"],
      ["P", "pause"],
      ["R", "restart"],
      ["Esc", "close"],
    ],
  },
  snake: {
    title: "Snake",
    hint: "Steer with arrows or WASD. Eat coral dots, avoid walls and your own tail.",
    keys: [
      ["Arrows / WASD", "steer"],
      ["P", "pause"],
      ["R", "restart"],
      ["Esc", "close"],
    ],
  },
};

// Set this to your repository URL after you push. Leave it empty and the
// "Source" links remove themselves, so the site never ships a dead link.
const REPO_URL = "";

for (const link of document.querySelectorAll("[data-repo-link]")) {
  if (REPO_URL) {
    link.href = REPO_URL;
  } else {
    (link.closest("[data-repo-block]") ?? link).remove();
  }
}

const stage = document.getElementById("stage");const stageTitle = document.getElementById("stage-title");
const stageHint = document.getElementById("stage-hint");
const keymap = document.getElementById("keymap");
const canvas = document.getElementById("canvas");
const bootOverlay = document.getElementById("boot-overlay");
const bootStatus = document.getElementById("boot-status");
const bootBar = document.getElementById("boot-bar");
const errorOverlay = document.getElementById("error-overlay");
const errorText = document.getElementById("error-text");
const leaveButton = document.getElementById("leave");
const runtimeStatus = document.getElementById("runtime-status");

let active = null;
let starting = false;

function renderKeymap(keys) {
  keymap.replaceChildren(
    ...keys.map(([key, label]) => {
      const row = document.createElement("div");
      const kbd = document.createElement("kbd");
      kbd.textContent = key;
      const span = document.createElement("span");
      span.textContent = label;
      row.append(kbd, span);
      return row;
    }),
  );
}

function showError(error) {
  console.error(error);
  const text = error?.message ? String(error.message) : String(error);
  errorText.textContent = text.slice(0, 4000);
  bootOverlay.hidden = true;
  errorOverlay.hidden = false;
  if (runtimeStatus) {
    runtimeStatus.textContent = "Runtime error — see the message above.";
    runtimeStatus.classList.remove("is-ready");
    runtimeStatus.classList.add("is-error");
  }
}

function setProgress(text, fraction) {
  bootStatus.textContent = text;
  bootBar.style.width = `${Math.max(0, Math.min(1, fraction ?? 0)) * 100}%`;
}

/**
 * Open a game. The first call downloads the runtime; later calls reuse it and
 * only swap the Python scene, which is why the second game starts instantly.
 */
async function play(slug) {
  const game = GAMES[slug];
  if (!game || starting) return;

  starting = true;
  unlockAudio(); // must happen inside the click gesture

  active = slug;
  document.body.dataset.game = slug;
  writeSlug(slug);
  stage.hidden = false;
  stageTitle.textContent = game.title;
  stageHint.textContent = game.hint;
  renderKeymap(game.keys);
  stage.scrollIntoView({ behavior: "smooth", block: "start" });
  canvas.focus({ preventScroll: true });

  try {
    if (!isBooted()) {
      bootOverlay.hidden = false;
      errorOverlay.hidden = true;
      setProgress("Warming up…", 0.02);
      await boot({ onProgress: setProgress });
      console.info("[main] boot resolved");
      bootOverlay.hidden = true;
      if (runtimeStatus) {
        runtimeStatus.textContent = "Runtime ready — Python 3.14 in WebAssembly.";
        runtimeStatus.classList.remove("is-error");
        runtimeStatus.classList.add("is-ready");
      }
    }

    switchGame(slug); // imports once, then resets the scene for a fresh round
    startLoop(showError);
    console.info("[main] game started", slug);
    enableControls((action) => {
      if (action === "escape") {
        closeStage();
      } else {
        press(action);
      }
    });
  } catch (error) {
    showError(error);
  } finally {
    starting = false;
  }
}

/** Hide the stage and stop requesting frames. The Python runtime stays warm. */
function closeStage() {
  stopLoop();
  disableControls();
  active = null;
  stage.hidden = true;
  document.body.dataset.game = "";
  writeSlug(null);
}

leaveButton.addEventListener("click", closeStage);

// Whole-card clicks play the game; the explicit button is the accessible path.
for (const card of document.querySelectorAll(".card[data-game]")) {
  card.addEventListener("click", (event) => {
    if (event.target.closest("a, button")) return;
    play(card.dataset.game);
  });
}

for (const button of document.querySelectorAll("[data-play]")) {
  button.addEventListener("click", () => play(button.dataset.play));
}

// A shared link like #/play/snake highlights the card but does not auto-download
// the runtime — the visitor still chooses when to spend the ~12 MB.
const deepLink = currentSlug();
if (deepLink && GAMES[deepLink]) {
  const card = document.querySelector(`.card[data-game="${deepLink}"]`);
  card?.classList.add("is-highlighted");
  card?.scrollIntoView({ block: "center" });
}

// Expose the current runtime version for the footer/tooling without another fetch.
export { GAMES };

// Small debug handle: handy in DevTools and for browser smoke tests.
window.__arcade = { isBooted, play, closeStage };
