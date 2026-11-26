# How this site works

Developer notes for this repository. The live site shows only the games; this
file is the map of what runs where and what each main function does.

## Pages

| URL | File | Purpose |
|---|---|---|
| `/` | `index.html` | Landing page: hero and three game cards. No runtime download. |
| `/snake/` | `snake/index.html` | Standalone Snake page. |
| `/tic-tac-toe/` | `tic-tac-toe/index.html` | Standalone Tic-Tac-Toe page. |
| `/2048/` | `2048/index.html` | Standalone 2048 page (Python module `games/twenty48`). |

The pages are plain static files, not a single-page app. A card is a normal
link, the browser back button works, and each game page has an “All games” link
back to `/`.

Each game page boots the Python runtime on load and shows a progress overlay
until the first frame is ready. The landing page never loads Python.

## The layers

| Layer | Files | Runs where |
|---|---|---|
| Page shell (HTML/CSS) | `index.html`, `snake/index.html`, `tic-tac-toe/index.html`, `2048/index.html`, `src/site.css` | Browser DOM |
| Loader and frame driver | `src/loader.js`, `src/game.js` | Browser JS |
| Home page setup | `src/home.js` | Browser JS |
| Input | `src/controls.js` | Browser JS |
| Python runtime | Pyodide + `pygame-ce` from jsDelivr | WebAssembly |
| Engine | `python/arcade/*` | WebAssembly |
| Game rules (pure) | `python/games/*/logic.py`, `ai.py` | WebAssembly **and** your laptop |
| Game scenes (pygame) | `python/games/*/scene.py` | WebAssembly **and** your laptop |
| Tests | `tests/*.py` | Your laptop / CI only |

The important split: **rules never import pygame**. `logic.py` is tested under
plain CPython in milliseconds, and `scene.py` is the only place that knows about
pixels, keys and timers.

## Boot sequence

Everything starts when a game page opens:

1. `src/game.js` runs, reads the slug from `<body data-game="…">`, and enables
   keyboard input. Escape works even while the game is loading.
2. `boot()` dynamically imports `pyodide.mjs` from the pinned CDN URL
   (`PYODIDE_VERSION` in `src/loader.js`).
3. `loadPyodide()` starts CPython 3.14 in WebAssembly.
4. `pyodide._api._skip_unwind_fatal_error = true` opts into Pyodide's SDL
   compatibility path. It is guarded because the hook is private API.
5. `pyodide.canvas.setCanvas2D(document.getElementById("canvas"))` binds the one
   `<canvas>` element. **This must happen before pygame is imported** — SDL reads
   the canvas during `set_mode()`.
6. `loadPackage("pygame-ce")` downloads the pygame wheel from the Pyodide CDN.
7. `loadProgram()` reads `manifest.json` (cache-busted with `?t=`), fetches every
   Python file listed there, and writes each one into Pyodide's in-memory
   filesystem under `/app/…`.
8. `sys.path.insert(0, "/app/python")`, then `pyimport("boot")` imports the entry
   module. Importing it runs the top-level code: display and font init,
   `set_mode((720, 720))`, and construction of the `App`.
9. `switchGame(slug)` builds the page's scene, the overlay is hidden, and
   `startLoop()` begins requesting frames.

Why a manifest instead of a wheel? A wheel is the right answer for a large
library, but this project is a handful of small files. A plain list keeps the
deployment "push files to GitHub Pages" and makes it obvious which modules ship.

## The frame loop

```text
requestAnimationFrame(now)
  dt = min((now - last) / 1000, 0.05)      # loader.js clamps tab-switch spikes
  api.arcade_frame(dt)                     # one synchronous Python call
      pygame.event.pump()                  # keep SDL's event queue healthy
      App.frame(dt)
          drain InputQueue                   # actions + canvas taps
          scene.update(dt)                   # pause-aware; scene decides timing
          scene.draw(screen)                 # render() + overlays
          pygame.display.flip()              # present to the canvas
```

**Why `requestAnimationFrame` instead of an `asyncio` loop.** The common Pyodide
recipe is `while True: … await asyncio.sleep(1/60)`. That works, but the loop
becomes a task you must pause, resume, cancel and recreate, and an uncaught
exception silently kills rendering. One JS callback per frame means Python can
never block the tab, pausing is `cancelAnimationFrame`, and `startLoop` can catch
the exception and show it in the error overlay.

**Why the dt clamp.** When a tab is hidden the browser throttles or stops
`requestAnimationFrame`. On return, the first `dt` can be many seconds. The clamp
(`0.05` s) plus `FixedStep.max_frame` (`0.25` s) prevents a burst of simulation
ticks.

## Main functions

### JavaScript — `src/loader.js`

| Function | Responsibility |
|---|---|
| `boot({ onProgress })` | One-time runtime setup. Shares a single promise, resets on failure so Reload can retry. Returns the Python `boot` module proxy. |
| `loadProgram(onProgress)` | Fetches `manifest.json` and each file, creates directories, writes bytes into `/app`, registers `/app/python` on `sys.path`. |
| `mkdirTree(path)` | Creates the `/app/...` directory chain before `FS.writeFile`. |
| `isBooted()` | Whether the runtime is ready (used to skip the download on later calls in the same page). |
| `switchGame(slug)` | Calls Python `boot.switch_game(slug)`. Imports the game module once, then resets the scene. |
| `press(action)` | Queues a string action (`"left"`, `"pause"`, …) into `InputQueue`. |
| `pointerDown(x, y)` | Queues a canvas tap already converted to 720×720 coordinates. |
| `startLoop(onError)` | Requests one Python frame per animation frame; on exception stops the loop and reports it. |
| `stopLoop()` | Cancels the pending frame. |

### JavaScript — page and input

| Function | File | Responsibility |
|---|---|---|
| `start()` | `src/game.js` | Enables input, boots if needed, switches to this page's game, starts frames. |
| `setProgress()` | `src/game.js` | Updates the loading overlay text and bar. |
| `showError(error)` | `src/game.js` | Stops the overlay and prints the Python traceback in the error card. |
| `goHome()` | `src/game.js` | Navigates to `../` — used by Escape. |
| `REPO_URL` | `src/home.js` | One place to set the GitHub link; empty means the link removes itself. |
| `enableControls(send)` | `src/controls.js` | Maps keys to actions and attaches the keyboard listener. |
| `disableControls()` | `src/controls.js` | Removes that listener on `pagehide`. |
| `canvasPoint(canvas, event)` | `src/controls.js` | Converts a pointer position on the CSS-scaled canvas back to 720×720. |

A game page is a real page: there is no router, no `#/play/...` hash and no
in-page stage. The back link and browser history do the navigation.

### Python — `python/boot.py`

| Function | Responsibility |
|---|---|
| Module import | `pygame.display.init()`, `pygame.font.init()`, `set_mode((720, 720))`, build the `App`. Audio is deliberately not initialized. |
| `switch_game(slug)` | Selects the game then resets it, so every page load starts a fresh round. |
| `press(action)` | Forwards an action string into `App.input`. |
| `pointer_down(x, y)` | Forwards a canvas tap into `App.input`. |
| `arcade_frame(dt)` | The whole visible frame: pump SDL, then `App.frame(dt)`. |

### Python — engine (all importable without a browser)

| Function / class | File | Responsibility |
|---|---|---|
| `App.switch(slug)` | `arcade/app.py` | Imports `games.<slug>.scene` lazily and calls its `build_scene()` factory. |
| `App.reset_scene()` | `arcade/app.py` | Fresh round; clears queued input. |
| `App.frame(dt)` | `arcade/app.py` | Drains input, updates, draws, flips the display. The one place the frame order is defined. |
| `BaseScene.handle_action(action)` | `arcade/scene.py` | Global behavior first: pause, restart, “action” after game over; then the game hook. |
| `BaseScene.pointer_down(x, y)` | `arcade/scene.py` | Ignores taps while paused; restarts after a finish once the grace period passes; otherwise calls `on_pointer`. |
| `BaseScene.update(dt)` | `arcade/scene.py` | Advances `time` and calls `tick(dt)` unless paused. Finished scenes keep animating. |
| `BaseScene.draw(surface)` | `arcade/scene.py` | Calls the game's `render()`, then draws the pause overlay. |
| `BaseScene.finish()` | `arcade/scene.py` | Marks the round over and starts a 0.55 s tap-to-restart cooldown. |
| `on_action` / `on_pointer` / `tick` / `render` | `arcade/scene.py` | Hooks a game implements. |
| `InputQueue.push_action/push_pointer` | `arcade/input.py` | Bounded queues (32 actions, 8 taps) so a background tab cannot replay a flood. |
| `FixedStep.advance(dt, interval)` | `arcade/timing.py` | Turns variable frame time into a number of fixed simulation ticks. |
| `HighScores.get/set` | `arcade/storage.py` | JSON in `localStorage` under `classic-games.v1`; in-memory fallback. |
| `Fonts`, `text`, `panel`, `overlay`, `lerp_color` | `arcade/theme.py` | One palette and the drawing helpers shared by the games. |

## Input pipeline

```text
keydown (browser) ─┐
touch button ──────┼─> controls.js maps to "left" | "up" | "pause" | ...
canvas pointerdown ──> canvasPoint() in 720×720 ──> pointerDown(x, y)
                        │
                        v
              loader.press / pointerDown
                        │
                        v
              boot.press -> InputQueue (Python)
                        │
              App.frame drains once per frame
                        │
                        v
              scene.handle_action / scene.pointer_down
```

Keyboard input deliberately does **not** go through SDL. Mapping keys in JS lets
us call `preventDefault()` (so arrows don't scroll the page), handle touch
buttons through the identical path, and avoid focus quirks. `pygame.event.pump()`
is still called each frame to keep SDL's window/event machinery healthy.

Escape is special: `game.js` intercepts it and navigates home instead of sending
it to Python.

## Timing model

Two clocks are in play:

- **Render clock** — `requestAnimationFrame`, typically 60–144 Hz. Drives
  animation, the food pulse and status text.
- **Simulation clock** — a fixed interval per game. Snake uses
  `max(0.065, 0.135 - 0.0005 × score)` seconds per grid move. Tic-Tac-Toe and
  2048 are turn-based: the AI delay (0.45 s) and player input are the only
  things that advance them, so they do not use `FixedStep` at all.

`FixedStep.advance` accumulates real `dt` (capped at 0.25 s), subtracts whole
intervals (at most 8 per frame), and returns the tick count. The leftover time is
available as `FixedStep.remainder`.

## Snake: wrapping and interpolation

The board is a torus. `logic.step` computes the next head with modulo:

```python
head = ((x + dx) % cols, (y + dy) % rows)
```

So moving off the right edge enters at the left, and the only way to die is
hitting your own body. Self-collision is checked against the body, except the
tail on a non-eating move (the tail vacates that tick).

Because a wrapped head jumps from cell 21 to cell 0, the scene does not draw raw
grid cells directly. Instead:

1. Before every grid tick, `SnakeScene` stores `_prev_body`.
2. `_tick_fraction()` returns `FixedStep.remainder / interval` — how far the
   current tick is toward the next snapshot.
3. `_body_positions()` interpolates every segment from its previous cell to its
   current cell. For a wrapped segment it emits **two** positions: one leaving
   the old edge, one arriving on the opposite edge.
4. `_draw_snake()` clips the whole draw to the board rectangle and then blits the
   rounded segments, so the departing copy is cut off at the wall while the
   arriving copy grows in on the other side.
5. Eyes are drawn at the interpolated head position on both copies (the clipped
   one is usually invisible). The result is a snake that visibly slides across
   the seam instead of teleporting.

If the state is replaced externally (tests, screenshots), `_body_positions()`
falls back to no interpolation when the previous body length does not match, so
a custom board never renders stale positions.

## 2048: one move, four transforms

2048 has no clock and no pixels in its rules. `logic.move(board, direction)`
returns `(new_board, points, changed)`:

1. Split the board into rows.
2. Transform so the requested direction becomes “left”:
   **right** reverses every row, **up** transposes, **down** transposes and
   reverses.
3. Slide each line left: drop zeros, merge equal neighbours once, drop zeros
   again.
4. Undo the transform.

`logic.slide(state, direction, rng)` is the game rule around that pure function:
if nothing moved it returns the same state (no spawn, no score), otherwise it
adds the merge points, spawns exactly one tile, and recomputes `over` with
`can_move`. The scene only maps actions to directions; all the interesting
behaviour is testable under plain CPython.

## Determinism and tests

Every rule module takes its randomness as an argument:

```python
state = logic.create_state(rng=Random(7))   # food placement is reproducible
```

That is what makes these tests meaningful:

| Test file | Proves |
|---|---|
| `tests/test_snake_logic.py` | Movement, turn buffering, growth, wrapping in both axes, seam self-collision, tail-vacate rule, speed floor, seeded determinism. |
| `tests/test_tictactoe_logic.py` | Board transitions, wins in every direction, draw detection. |
| `tests/test_tictactoe_ai.py` | Perfect play draws from the empty board; the AI takes wins, blocks losses, and never loses in 120 games against random. |
| `tests/test_2048_logic.py` | Seeded openings, one-merge-per-pair, all four directions, spawn-only-on-change, dead-board detection. |
| `tests/test_scenes.py` | Every draw call and the real input pipeline, headless (`SDL_VIDEODRIVER=dummy`), including self-collision, both sides of a wrap, and a 2048 restart. |
| `tests/test_engine.py` | Queue bounds, fixed-step math, score persistence. |

Run them with:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## Adding a game

1. Create `python/games/<slug>/` with `constants.py`, `logic.py` (pure rules)
   and `scene.py` exposing `build_scene(screen, fonts, scores)`. The packages
   are implicit namespace packages — no `__init__.py`, which is also what lets
   Jekyll serve them (it drops underscore-prefixed files).
2. Register the files in `manifest.json` and bump its `version` (cache bust).
3. Create `<url-slug>/index.html` based on an existing game page, set
   `<body data-game="<slug>">`, and add a card in `index.html`.
4. Add `docs/games/<slug>.md` and link it from this file and the README.
5. Add rules tests; extend `tests/test_scenes.py` with a headless draw/run test.

If a file is missing from `manifest.json`, the loader will never fetch it and
Python will fail with `ModuleNotFoundError` — that is the most common mistake.

## Deployment

The site is static. Two deployment paths exist, and it is worth knowing which
one is serving:

- **Branch build (currently live).** With Pages set to “Deploy from a branch”,
  GitHub runs Jekyll over `main` and serves the result. `_config.yml` excludes
  `docs/`, `screenshots/`, `tests/`, `tools/`, the README and dev requirements,
  so only the runtime files are published.
- **Actions artifact.** `.github/workflows/deploy.yml` installs dev
  dependencies, runs `pytest` (a failing test blocks the deploy), stages the
  runtime files into `_site/`, and uploads that folder as the Pages artifact.
  This path takes over when Pages is set to “GitHub Actions”.

The Python packages are implicit namespace packages — there are no
`__init__.py` files. That is deliberate: Jekyll silently drops files whose names
start with an underscore, which used to make every Python import fail on the
live site.

Live site: <https://salman2843.github.io/classic-arcade/>

Notes:

- Everything is referenced with relative paths, so the site works at both
  `username.github.io` and `username.github.io/repo-name/`.
- Pyodide, its standard library and the pygame wheel come from jsDelivr, not from
  your Pages quota. Your bandwidth serves only the shell plus a few dozen KB of
  Python.
- Each game page boots its own runtime. The WASM and wheel are cached by the
  browser, so the second game page is much faster than the first.
- `manifest.json` is fetched with a timestamp; its `version` is appended to every
  module URL. Bump the version when you change Python code or users may see a
  cached module.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Canvas stays black, console mentions a missing canvas | The SDL canvas must keep `id="canvas"`. `setCanvas2D` runs before `pygame` import in `src/loader.js`. |
| `Could not load python/… (HTTP 404)` | File missing from the repo or from `manifest.json`; check case-sensitivity on Pages. If it is an `__init__.py`, delete it — the packages are namespace packages and Jekyll drops underscore files. |
| `/snake/` returns 404 locally or on Pages | The page must live at `snake/index.html`; the folder is what makes the pretty URL work. |
| Change deployed but behaviour is old | Bump `manifest.json` → `version`, hard-reload once. |
| “The game stopped” overlay with a traceback | A Python exception escaped a frame; the overlay prints the traceback. The loop stops instead of freezing the tab. |
| Page feels frozen while a game loads | Expected on first boot (runtime download). Progress is shown in the overlay. |
| Touch D-pad missing | It only appears for Snake and 2048 on coarse pointers; desktop uses the keyboard. |
| No sound | Not implemented yet; initialize `pygame.mixer` after a user gesture when adding it. |

## Known limits

- SDL support in Pyodide is explicitly experimental. The Pyodide version is
  pinned in `src/loader.js`; upgrading it is a deliberate, tested change.
- A Pyodide instance can target exactly one canvas. Each game page is its own
  instance, so this is a non-issue.
- There are no threads. Keep per-frame work small: no network or disk I/O inside
  `render()`/`tick()`.
- The first game page downloads roughly 12 MB. The runtime is not bundled into
  the repository.

## Version pins

| Thing | Version | Where |
|---|---|---|
| Pyodide | `314.0.8` | `PYODIDE_VERSION`, `src/loader.js` |
| CPython (browser) | `3.14.2` | inside Pyodide |
| pygame-ce (browser) | `2.5.7` | Pyodide package index |
| pygame-ce (desktop dev) | `2.5.8` | `requirements-dev.txt` |
| Python (tests/CI) | 3.13+ | `actions/setup-python` |
