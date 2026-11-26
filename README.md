# Arcade / Classic

Three browser games — two arcade classics and a puzzle — built with
**pygame-ce** and running entirely in the browser through **Pyodide** (CPython
compiled to WebAssembly). Plain static hosting on GitHub Pages — no backend, no
database, no build step for the games.

**Play it live:** https://salman2843.github.io/classic-arcade/

- **Tic-Tac-Toe** — you are X against a minimax opponent that never blunders.
  → https://salman2843.github.io/classic-arcade/tic-tac-toe/
- **Snake** — eat, grow, and wrap through the walls to the other side.
  → https://salman2843.github.io/classic-arcade/snake/
- **2048** — slide, merge, and build a tile worth 2048.
  → https://salman2843.github.io/classic-arcade/2048/

Scores and win/loss records are stored in the browser (`localStorage`), so there
is nothing to sign up for and no server to run.

| Tic-Tac-Toe | Snake | 2048 |
|---|---|---|
| ![Tic-Tac-Toe, diagonal win](screenshots/tictactoe.png) | ![Snake crossing the wrap seam](screenshots/snake.png) | ![A 2048 board part-way through a run](screenshots/2048.png) |

All three images are rendered from the real pygame scenes by
`tools/screenshots.py` (`SDL_VIDEODRIVER=dummy`), so they double as a visual
smoke test.

## Pages

| URL | File | Loads Python? |
|---|---|---|
| `/` | `index.html` | No — landing page only |
| `/snake/` | `snake/index.html` | Yes, on page load |
| `/tic-tac-toe/` | `tic-tac-toe/index.html` | Yes, on page load |
| `/2048/` | `2048/index.html` | Yes, on page load |

Each game page is standalone: it boots the runtime, starts its one game, and
shows an **All games** link back to `/`. The landing page only links to the game
pages, so a visitor can read it without downloading anything.

## How it works

- Game **rules** are pure Python (`logic.py`, `ai.py`) with no pygame import, so
  `pytest` plays them in milliseconds without a browser.
- **Scenes** (`scene.py`) own pygame drawing, timing and input mapping.
- A small JS loader boots Pyodide once per page, copies the Python files into
  Pyodide's in-memory filesystem, and drives one Python frame per
  `requestAnimationFrame`.
- The same Python code runs on a laptop (desktop pygame window in `tools/`) and
  in the browser, which is what makes the headless tests meaningful.

More detail: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Layout

```text
index.html                 landing page: hero + three game cards
snake/index.html           standalone Snake page
tic-tac-toe/index.html     standalone Tic-Tac-Toe page
2048/index.html            standalone 2048 page
src/loader.js              Pyodide boot, module loading, rAF frame loop
src/game.js                game-page lifecycle: boot, switch, frames, errors
src/home.js                points the GitHub link at your repo
src/controls.js            keyboard / touch / canvas taps -> actions
src/site.css               shared styling for the home and game pages
python/boot.py             entry point imported inside Pyodide
python/arcade/             engine: App, BaseScene, InputQueue, FixedStep, storage
python/games/snake/        logic.py (pure) + scene.py (pygame)
python/games/tictactoe/    logic.py + ai.py (pure) + scene.py (pygame)
python/games/twenty48/     2048: logic.py (pure) + scene.py (pygame)
tests/                     pytest: rules, AI, headless scene smoke tests
docs/                      developer notes (kept in the repo, not on the site)
screenshots/               rendered by tools/screenshots.py (README + docs)
tools/dev_run.py           desktop pygame runner
tools/screenshots.py       headless renderer / visual smoke test
manifest.json              list of Python files shipped to the browser
```

## Run locally

ES modules and `fetch` do not work from `file://`, so use a static server:

```powershell
git clone https://github.com/salman2843/classic-arcade.git
cd classic-arcade
python -m http.server 8000
# open http://localhost:8000
```

The first game page downloads roughly 12 MB of runtime from the Pyodide CDN;
the browser caches it for later visits. Everything else is served from the repo.

### Tests

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

56 tests cover the rules, the minimax AI, the 2048 merges, the input queue,
fixed-step timing, score persistence, and every draw call in all three scenes
(headless SDL).

### Desktop and screenshots

```powershell
# play the exact scene in a desktop pygame window, for debugging
.\.venv\Scripts\python.exe tools\dev_run.py snake
.\.venv\Scripts\python.exe tools\dev_run.py tictactoe

# re-render screenshots/ from the real scenes (headless)
.\.venv\Scripts\python.exe tools\screenshots.py
```

## Deployment

Deployment is fully automated by
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) on every push to
`main`:

1. Install dev dependencies (pip cache keyed to `requirements-dev.txt`).
2. Run `pytest -q`. A failing test stops the deploy.
3. Stage only the runtime files into `_site/`:
   `index.html`, `manifest.json`, `src/`, `python/`, `snake/`,
   `tic-tac-toe/`, `2048/`, plus `.nojekyll`.
4. Configure Pages (the workflow asks GitHub to create the Pages site if it does
   not exist yet).
5. Upload `_site/` as the Pages artifact and deploy it.

`docs/` and `screenshots/` are intentionally **not** published: they are
developer material and stay on GitHub. There is no docs build step; the `.md`
files are read directly in the repo.

### One-time repository setup

1. Open **Settings → Pages** for the repository.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Push to `main` (or re-run the latest **Deploy site** workflow).

The workflow passes `enablement: true` to `actions/configure-pages`, so it can
usually create the Pages site itself. If the token is not allowed to, the run
fails at that step and the manual **Source: GitHub Actions** setting above fixes
it; then use **Re-run all jobs** on the failed run.

### Site URLs

- https://salman2843.github.io/classic-arcade/
- https://salman2843.github.io/classic-arcade/snake/
- https://salman2843.github.io/classic-arcade/tic-tac-toe/
- https://salman2843.github.io/classic-arcade/2048/

All paths are relative, so the same files work at
`username.github.io` or `username.github.io/repo-name/` without changes.

## Maintenance

- **Python changes:** bump `version` in `manifest.json`. Module URLs include
  that version, so otherwise browsers may keep using a cached copy.
- **JS/CSS changes:** normal browser caching applies; a hard reload shows the
  new files immediately.
- **GitHub link on the site:** set `REPO_URL` at the top of `src/home.js`. While
  it is empty, the link removes itself.
- **Runtime upgrades:** the Pyodide version is pinned in `src/loader.js`
  (`PYODIDE_VERSION`); keep it in sync with `docs/ARCHITECTURE.md`.
- **License:** add a `LICENSE` file (MIT is a good default for a portfolio).

## Developer notes

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — page structure, boot sequence,
  frame loop, main functions, testing and deployment.
- [`docs/games/snake.md`](docs/games/snake.md) — rules, wrap-around, animation.
- [`docs/games/tictactoe.md`](docs/games/tictactoe.md) — rules and minimax AI.
- [`docs/games/2048.md`](docs/games/2048.md) — board transforms, merges, scene.
