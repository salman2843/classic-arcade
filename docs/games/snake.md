# Snake

The grid classic with a twist: the board wraps. Slip off one edge and you come
back on the opposite side. Eat the coral dots, grow, and never bite your own
tail. The board is 22×22 cells of 28 px on a fixed 720×720 logical canvas.

![Snake crossing the wrap seam](../../screenshots/snake.png)

- Page: `/snake/` (`snake/index.html`).
- Controls: **arrows / WASD** steer, **P** pause, **R** restart, **Esc** back to
  all games.
- High score persists in `localStorage` under `classic-games.v1` → `snake.best`.
- Score: **10 points per dot**. Speed increases with score.

Source: `python/games/snake/` (`logic.py`, `scene.py`, `constants.py`).

## State

`SnakeState` is a frozen dataclass. `step()` returns a new state instead of
mutating the old one, so a test can keep the previous tick around and compare.

| Field | Type | Meaning |
|---|---|---|
| `cols`, `rows` | `int` | Board size in cells (default 22×22). |
| `body` | `tuple[Point, ...]` | Snake cells, **head first**, tail last. |
| `direction` | `(dx, dy)` | Direction of the last applied move. |
| `pending` | `tuple[Direction, ...]` | Buffered turns, max two, applied one per tick. |
| `food` | `Point \| None` | Current dot, or `None` on a full board. |
| `score` | `int` | 10 points per dot. |
| `alive` | `bool` | False after a self-collision. |
| `ticks` | `int` | Number of grid moves performed; used by tests. |

Directions are tuples: `RIGHT = (1, 0)`, `UP = (0, -1)` (y grows downward).

## Main functions

| Function | What it does | Why it is shaped this way |
|---|---|---|
| `create_state(cols, rows, rng)` | Builds a length-3 snake at the board centre, moving right, and places the first food. | RNG is injected, so `Random(7)` always produces the same board. |
| `random_empty_cell(state, rng)` | Uniformly chooses a cell not occupied by the snake. | Guarantees food never spawns under the body; returns `None` when full. |
| `queue_direction(state, direction)` | Appends a turn to `pending`. Rejects reversals, duplicates and a third buffered turn. | Two buffered turns let a fast “up then left” corner register inside one tick without allowing self-kill by pressing the opposite arrow. |
| `step(state, rng)` | One grid tick: wrap the head, move, eat/grow, check self-collision, respawn food. | Every rule lives here; rendering never changes state. |
| `interval_for(score)` | `max(0.065, 0.135 - 0.0005 × score)` seconds per tick. | The speed ramp is a pure formula, so it is trivial to test and tune. |

`scene.py` then holds only presentation concerns:

| Function | Responsibility |
|---|---|
| `build_scene(screen, fonts, scores)` | Factory used by `App.switch()`. |
| `SnakeScene.reset()` | New `SnakeState`, reset previous-body snapshot, clear accumulator, reload best score. |
| `SnakeScene.on_action(action)` | Maps `Action.LEFT/RIGHT/UP/DOWN` to `queue_direction`. |
| `SnakeScene.tick(dt)` | Asks `FixedStep` how many grid moves are due, snaps `_prev_body`, applies them, handles death. |
| `SnakeScene._tick_fraction()` | `FixedStep.remainder / interval` — how far the current frame is toward the next tick (0..1). |
| `SnakeScene._body_positions()` | Continuous grid positions for every segment, with two copies for a segment crossing an edge. |
| `SnakeScene._end_round()` | Updates `snake.best` and calls `finish()`. |
| `SnakeScene.render(surface)` | Board, food, snake, HUD, game-over overlay. |
| `SnakeScene._draw_snake()` | Draws the interpolated segments tail → head with a colour gradient, then two eyes based on direction. |

## One tick, in order

1. Take `pending[0]` as this tick’s direction (else keep `direction`).
2. Compute `head = ((x + dx) % cols, (y + dy) % rows)`.
3. **Self check:** the new head is in the body — except the tail, which vacates
   this tick *unless* the snake is eating.
4. Grow if the head lands on food (`score += 10`), otherwise drop the tail.
5. On eating, spawn the next food on a free cell.

There is no wall death: the modulo step is the wall rule. The tail rule still
matters — turning into the cell your tail is leaving is legal — and
`tests/test_snake_logic.py` locks both behaviours in.

## Wrapping and interpolation

Cell snapshots alone would make a wrapped head jump from x=21 to x=0. The scene
keeps one extra snapshot and smooths it out:

1. `tick()` stores `_prev_body` before each grid step.
2. `_tick_fraction()` says how much of the next tick has elapsed.
3. For each segment, `_body_positions()` interpolates `_prev_body[i] → body[i]`.
   When a segment crossed an edge, it emits two positions: one a little past the
   old edge and one a little past the opposite edge.
4. `_draw_snake()` clips to the board rectangle. The departing copy is cut off at
   the wall while the arriving copy grows in on the other side, so the snake
   visibly slides through the seam.
5. Eyes are drawn at the interpolated head position (on both copies, though the
   clipped one is usually invisible).

If `_prev_body` does not match the current body length (a test or screenshot
replaced the state), interpolation is skipped rather than drawing stale cells.

## Timing

The snake never moves once per rendered frame. `FixedStep.advance(dt, interval)`
accumulates real time and returns how many whole grid ticks are due:

```text
score 0    -> 0.135 s / move  (~7.4 moves per second)
score 70   -> 0.100 s / move  (~10 moves per second)
score 140+ -> 0.065 s / move  (~15 moves per second, floor)
```

A single frame can therefore run zero, one, or several grid moves. The JS loop
clamps `dt` to 0.05 s and `FixedStep` clamps the accumulated frame to 0.25 s
(max 8 ticks), so returning to a background tab cannot teleport the snake.

## Rendering notes

- The checkerboard is rendered **once** into `_board_art` and blitted each frame;
  redrawing 484 rects per frame would be wasteful inside WebAssembly.
- Segments are rounded rects with a colour lerp from `MINT_DARK` (tail) to `MINT`
  (head), so the direction of travel is readable at a glance.
- Food pulses with `sin(time × 7)`; the glow is a darker coral circle behind it.
- The game-over overlay shows score, best, a `NEW BEST` badge and a pulsing
  “Press R or tap to play again”. Tapping is handled by `BaseScene` with a
  0.55 s grace period.
- Pause is entirely inherited from `BaseScene`.

## Tuning

| Constant | File | Effect |
|---|---|---|
| `COLS`, `ROWS`, `CELL` | `constants.py` | Board size and pixel scale (616 px board, centred at x=52, y=76). |
| `BASE_INTERVAL` | `constants.py` | Starting seconds per move (0.135). |
| `MIN_INTERVAL` | `constants.py` | Speed floor (0.065). |
| `SPEED_PER_POINT` | `constants.py` | How fast the ramp is (0.0005 s per point). |
| `FOOD_SCORE` | `constants.py` | Points per dot (10). |
| `SEGMENT_INSET`, `SEGMENT_RADIUS` | `constants.py` | Segment look. |

## Tests

`tests/test_snake_logic.py` covers: seeded creation, single-cell movement,
reversal/duplicate rejection, buffered corners, growth + score + food respawn,
horizontal and vertical wrapping, seam self-collision, neck collision,
tail-vacate legality, dead snake immobility, speed floor/ceiling, and full
determinism for a seeded run.

`tests/test_scenes.py` drives the real scene headless, forces a self-collision,
restarts with a tap, checks pause freezes the tick counter, verifies restart
resets the round, and checks that a wrapped head is drawn on both sides of the
edge at the halfway point of a tick.

## Extensions worth trying

- **Solid walls mode** — keep the modulo step behind a flag and add the old
  out-of-bounds check for a “classic” mode next to the wrap mode.
- **Smooth corners** — interpolate along an L-shaped path instead of a straight
  line between cells, so turns look rounder at low speeds.
- **Obstacles** — add a `walls: frozenset[Point]` field and include it in both
  the collision check and `random_empty_cell`.
- **Swipe input** — map `pointermove` deltas in `controls.js` to the same four
  actions; the Python side needs no change.
- **SFX** — initialize `pygame.mixer` after a user gesture on the game page,
  then play OGG files on eat/death.
