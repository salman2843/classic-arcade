# How this site works

Two classic games, written in Python, running in the browser with no server.
This page is the map: what runs where, what each main function does, and what
happens between a Play click and a painted frame.

- **Tic-Tac-Toe** — [game notes](games/tictactoe.md)
- **Snake** — [game notes](games/snake.md)

## The layers

| Layer | Files | Runs where |
|---|---|---|
| Page shell (HTML/CSS) | `index.html`, `src/site.css` | Browser DOM |
| Loader and frame driver | `src/loader.js` | Browser JS |
| Input and routing | `src/controls.js`, `src/router.js`, `src/main.js` | Browser JS |
| Python runtime | Pyodide + `pygame-ce` from jsDelivr | WebAssembly |
| Engine | `python/arcade/*` | WebAssembly |
| Game rules (pure) | `python/games/*/logic.py`, `ai.py` | WebAssembly **and** your laptop |
| Game scenes (pygame) | `python/games/*/scene.py` | WebAssembly **and** your laptop |
| Tests | `tests/*.py` | Your laptop / CI only |

The important split: **rules never import pygame**. `logic.py` can be tested in
milliseconds under plain CPython, and `scene.py` is the only place that knows
about pixels, keys and timers.

## Boot sequence

Everything starts when the visitor presses a Play button. Nothing is downloaded
before that, so the landing page stays light.

1. `play(slug)` in `src/main.js` opens the stage, updates the URL hash, and calls
   `boot()` — once per page visit.
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
9. `switchGame(slug)` asks Python for the scene, and `startLoop()` begins
   requesting frames.

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
becomes a task you must pause, resume, cancel and recreate on every navigation,
and an uncaught exception silently kills rendering. One JS callback per frame
means Python can never block the tab, pausing is `cancelAnimationFrame`, and
`startLoop` can catch the exception and show it in the error overlay.

**Why the dt clamp.** When a tab is hidden the browser throttles or stops
`requestAnimationFrame`. On return, the first `dt` can be many seconds. The clamp
(`0.05` s) plus `FixedStep.max_frame` (`0.25` s) prevents a burst of simulation
ticks that would teleport the snake through a wall.

## Main functions

### JavaScript — `src/loader.js`

| Function | Responsibility |
|---|---|
| `boot({ onProgress })` | One-time runtime setup. Shares a single promise, resets on failure so Reload can retry. Returns the Python `boot` module proxy. |
| `loadProgram(onProgress)` | Fetches `manifest.json` and each file, creates directories, writes bytes into `/app`, registers `/app/python` on `sys.path`. |
| `mkdirTree(path)` | Creates the `/app/...` directory chain before `FS.writeFile`. |
| `isBooted()` | Whether the runtime is ready (used to skip the 12 MB download on later plays). |
| `switchGame(slug)` | Calls Python `boot.switch_game(slug)`. Imports the game module once, then resets the scene. |
| `press(action)` | Queues a string action (`"left"`, `"pause"`, …) into `InputQueue`. |
| `pointerDown(x, y)` | Queues a canvas tap already converted to 720×720 coordinates. |
| `startLoop(onError)` | Requests one Python frame per animation frame; on exception stops the loop and reports it. |
| `stopLoop()` | Cancels the pending frame. The Python runtime stays warm for instant resume. |

### JavaScript — the rest of the shell

| Function | File | Responsibility |
|---|---|---|
| `play(slug)` | `src/main.js` | Opens the stage, boots if needed, switches the scene, enables input. |
| `closeStage()` | `src/main.js` | Stops frames, disables input, clears the hash, hides the stage. |
| `showError(error)` / `setProgress()` | `src/main.js` | Feed the error overlay and boot progress bar. |
| `enableControls(send)` | `src/controls.js` | Maps keys to actions and attaches listeners while a game is open. |
| `disableControls()` | `src/controls.js` | Removes those listeners so they never pile up. |
| `canvasPoint(canvas, event)` | `src/controls.js` | Converts a pointer position on the CSS-scaled canvas back to 720×720. |
| `unlockAudio()` | `src/controls.js` | Creates/resumes an `AudioContext` inside the Play click (audio policy hook). |
| `currentSlug()` / `writeSlug()` | `src/router.js` | Read and replace the `#/play/<slug>` route. |

### Python — `python/boot.py`

| Function | Responsibility |
|---|---|
| Module import | `pygame.display.init()`, `pygame.font.init()`, `set_mode((720, 720))`, build the `App`. Audio is deliberately not initialized. |
| `switch_game(slug)` | Selects the game then resets it, so every Play press starts a fresh round. |
| `press(action)` | Forwards an action string into `App.input`. |
| `pointer_down(x, y)` | Forwards a canvas tap into `App.input`. |
| `arcade_frame(dt)` | The whole visible frame: pump SDL, then `App.frame(dt)`. |

### Python — engine (all importable without a browser)

| Function / class | File | Responsibility |
|---|---|---|
| `App.switch(slug)` | `arcade/app.py` | Imports `games.<slug>.scene` lazily and calls its `build_scene()` factory. |
| `App.reset_scene()` | `arcade/app.py` | Fresh round; clears queued input. |
| `App.frame(dt)` | `arcade/app.py` | Drains input, updates, draws, flips the display. The one place the frame order is defined. |
| `BaseScene.handle_action(action)` | `arcade/scene.py` | Global behavior first: pause, restart, "action" after game over; then the game hook. |
| `BaseScene.pointer_down(x, y)` | `arcade/scene.py` | Ignores taps while paused; restarts after a finish once the grace period passes; otherwise calls `on_pointer`. |
| `BaseScene.update(dt)` | `arcade/scene.py` | Advances `time` and calls `tick(dt)` unless paused. Finished scenes keep animating. |
| `BaseScene.draw(surface)` | `arcade/scene.py` | Calls the game's `render()`, then draws the pause overlay. |
| `BaseScene.finish()` | `arcade/scene.py` | Marks the round over and starts a 0.55 s tap-to-restart cooldown. |
| `on_action` / `on_pointer` / `tick` / `render` | `arcade/scene.py` | Hooks a game implements. |
| `InputQueue.push_action/push_pointer` | `arcade/input.py` | Bounded queues (32 actions, 8 taps) so a background tab cannot replay a flood. |
| `FixedStep.advance(dt, interval)` | `arcade/timing.py` | Turns variable frame time into a number of fixed simulation ticks. |
| `HighScores.get/set` | `arcade/storage.py` | JSON in `localStorage` under `classic-games.v1`; in-memory fallback. |
| `Fonts`, `text`, `panel`, `overlay`, `lerp_color` | `arcade/theme.py` | One palette and the drawing helpers shared by both games. |

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

## Timing model

Two clocks are in play:

- **Render clock** — `requestAnimationFrame`, typically 60–144 Hz. Drives
  animation, the food pulse and status text.
- **Simulation clock** — a fixed interval per game. Snake uses
  `max(0.065, 0.135 - 0.0005 × score)` seconds per grid move; Tic-Tac-Toe is
  turn-based and uses a 0.45 s AI "thinking" delay instead.

`FixedStep.advance` accumulates real `dt` (capped at 0.25 s), subtracts whole
intervals (at most 8 per frame), and returns the tick count. Consequences:

- The snake moves at the same speed on a 60 Hz and a 144 Hz display.
- The 0.05 s clamp in JS plus the 0.25 s cap in Python prevent catch-up spirals.
- A tick's leftover time is available as `FixedStep.remainder` for future
  interpolation.

## Determinism and tests

Every rule module takes its randomness as an argument:

```python
state = logic.create_state(rng=Random(7))   # food placement is reproducible
```

That is what makes these tests meaningful:

| Test file | Proves |
|---|---|
| `tests/test_snake_logic.py` | Movement, turn buffering, growth, wall/self death, tail-vacate rule, speed floor, seeded determinism. |
| `tests/test_tictactoe_logic.py` | Board transitions, wins in every direction, draw detection. |
| `tests/test_tictactoe_ai.py` | Perfect play draws from the empty board; the AI takes wins, blocks losses, and never loses in 120 games against random. |
| `tests/test_scenes.py` | Every draw call and the real input pipeline, headless (`SDL_VIDEODRIVER=dummy`). |
| `tests/test_engine.py` | Queue bounds, fixed-step math, score persistence. |

Run them with:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## Adding a game

1. Create `python/games/<slug>/` with `__init__.py`, `constants.py`,
   `logic.py` (pure rules) and `scene.py` exposing
   `build_scene(screen, fonts, scores)`.
2. Register the files in `manifest.json` and bump its `version` (cache bust).
3. Add a card in `index.html` with `data-game` / `data-play`, and an entry in the
   `GAMES` object in `src/main.js` for its title, hint and control legend.
4. Add `docs/games/<slug>.md` and list it in `PAGES` in `tools/build_docs.py`.
5. Add rules tests; extend `tests/test_scenes.py` with a headless draw/run test.

If a file is missing from `manifest.json`, the loader will never fetch it and
Python will fail with `ModuleNotFoundError` — that is the most common mistake.

## Deployment

The site is static. The GitHub Actions workflow (`.github/workflows/deploy.yml`)
does:

1. Install dev dependencies.
2. Run `pytest` — a failing test blocks the deploy.
3. Render Markdown docs to HTML (`tools/build_docs.py`).
4. Copy the runtime files into `_site/` (`index.html`, `src/`, `python/`,
   `manifest.json`, `docs/`, `screenshots/`, `.nojekyll`).
5. Upload the folder as a Pages artifact and deploy it.

One-time setup: **Settings → Pages → Source: GitHub Actions**, then push to
`main`.

Notes:

- Everything is referenced with relative paths, so the site works at both
  `username.github.io` and `username.github.io/repo-name/`.
- Pyodide, its standard library and the pygame wheel come from jsDelivr, not from
  your Pages quota. Your bandwidth serves only the shell plus a few dozen KB of
  Python.
- First launch downloads roughly 12 MB. Later visits and later games reuse the
  browser cache and the already-booted runtime.
- `manifest.json` is fetched with a timestamp; its `version` is appended to every
  module URL. Bump the version when you change Python code or users may see a
  cached module.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Canvas stays black, console mentions a missing canvas | The SDL canvas must keep `id="canvas"`. `setCanvas2D` runs before `pygame` import in `src/loader.js`. |
| `Could not load python/… (HTTP 404)` | File missing from the repo or from `manifest.json`; check case-sensitivity on Pages. |
| Change deployed but behaviour is old | Bump `manifest.json` → `version`, hard-reload once. |
| "The runtime stopped" overlay with a traceback | A Python exception escaped a frame; the overlay prints the traceback. The loop stops instead of freezing the tab. |
| Page feels frozen while a game loads | Expected on first boot (runtime download). Progress is shown in the overlay. |
| Touch D-pad missing | It only appears for `body[data-game="snake"]` on coarse pointers; desktop uses the keyboard. |
| No sound | Intentionally not implemented yet; `unlockAudio()` in `controls.js` is the ready hook. |

## Known limits

- SDL support in Pyodide is explicitly experimental. The Pyodide version is
  pinned in `src/loader.js`; upgrading it is a deliberate, tested change.
- A Pyodide instance can target exactly one canvas, so the site has one shared
  stage rather than one canvas per game.
- There are no threads. Keep per-frame work small: no network or disk I/O inside
  `render()`/`tick()`.
- The first load is ~12 MB. The runtime is not bundled into the repository.

## Version pins

| Thing | Version | Where |
|---|---|---|
| Pyodide | `314.0.8` | `PYODIDE_VERSION`, `src/loader.js` |
| CPython (browser) | `3.14.2` | inside Pyodide |
| pygame-ce (browser) | `2.5.7` | Pyodide package index |
| pygame-ce (desktop dev) | `2.5.8` | `requirements-dev.txt` |
| Python (tests/CI) | 3.13+ | `actions/setup-python` |
