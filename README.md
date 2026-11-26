# Arcade / Classic

Two classic games built with **pygame-ce** and running entirely in the browser
through **Pyodide** (CPython 3.14 compiled to WebAssembly). Static hosting on
GitHub Pages — no backend, no build step for the games.

- **Tic-Tac-Toe** — you are X against a perfect minimax opponent.
- **Snake** — eat, grow, and wrap through the walls to the other side.

| Tic-Tac-Toe | Snake |
|---|---|
| ![Tic-Tac-Toe, diagonal win](screenshots/tictactoe.png) | ![Snake crossing the wrap seam](screenshots/snake.png) |

Both images are rendered from the real pygame scenes by
`tools/screenshots.py` (`SDL_VIDEODRIVER=dummy`), so they double as a visual
smoke test.

## Pages

- `/` — landing page with the two game cards.
- `/snake/` — the Snake game page.
- `/tic-tac-toe/` — the Tic-Tac-Toe game page.

Each game page is standalone: it loads only its own game, shows a back link, and
the runtime starts when the page opens. The landing page itself downloads no
Python.

## Why this stack

- One language for rules, rendering and tests.
- Game rules are pure Python, so `pytest` plays them without a browser.
- The games run from plain static files; GitHub Pages hosts the site for free.

The trade-off is a ~12 MB runtime download on the first game page. The browser
cache makes later visits fast.

## Run it

```powershell
# static server (needed: ES modules and fetch do not work from file://)
python -m http.server 8000
# open http://localhost:8000
```

```powershell
# tests (creates an isolated environment)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

```powershell
# same scene in a desktop pygame window, for debugging
.\.venv\Scripts\python.exe tools\dev_run.py snake
.\.venv\Scripts\python.exe tools\dev_run.py tictactoe
```

```powershell
# re-render screenshots/ from the real scenes (headless)
.\.venv\Scripts\python.exe tools\screenshots.py
```

## Layout

```text
index.html                 landing page: hero + two game cards
snake/index.html           standalone Snake page
tic-tac-toe/index.html     standalone Tic-Tac-Toe page
src/loader.js              Pyodide boot, module loading, rAF frame loop
src/game.js                game-page lifecycle: boot, switch, frames, errors
src/home.js                points the GitHub link at your repo
src/controls.js            keyboard / touch / canvas taps -> actions
python/boot.py             entry point imported inside Pyodide
python/arcade/             engine: App, BaseScene, InputQueue, FixedStep, storage
python/games/snake/        logic.py (pure) + scene.py (pygame)
python/games/tictactoe/    logic.py + ai.py (pure) + scene.py (pygame)
tests/                     pytest: rules, AI, headless scene smoke tests
docs/                      developer notes (kept in the repo, not on the site)
screenshots/               rendered by tools/screenshots.py (README + docs)
tools/dev_run.py           desktop pygame runner
tools/screenshots.py       headless renderer / visual smoke test
manifest.json              list of Python files shipped to the browser
```

## Deploy

1. Push the repository to GitHub.
2. **Settings → Pages → Source: GitHub Actions**.
3. Push to `main`. `.github/workflows/deploy.yml` runs the tests and publishes
   the site.

Everything uses relative paths, so it works on a project page
(`username.github.io/repo/`) or a user page without changes.

## Before you publish

- Set `REPO_URL` at the top of `src/home.js` to your repository URL. While it is
  empty, the GitHub link removes itself.
- Optional: add a `LICENSE` file (MIT is a good default for a portfolio).
- If you change Python code, bump `version` in `manifest.json` so browsers fetch
  the new modules instead of a cached copy.

## Developer notes

The site is intentionally user-facing only. These notes live here on GitHub:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — page structure, boot sequence,
  frame loop, main functions, testing and deployment.
- [`docs/games/snake.md`](docs/games/snake.md) — rules, wrap-around, animation.
- [`docs/games/tictactoe.md`](docs/games/tictactoe.md) — rules and minimax AI.
