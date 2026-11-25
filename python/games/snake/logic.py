"""Snake rules: pure, deterministic, and independent of pygame.

The board is a grid of integer cells; the state is a frozen dataclass, so each
``step`` returns a brand-new state. The only outside influence is the injected
``random.Random`` used to place food, which makes seeded tests exact.

Coordinate system: x grows right, y grows down, origin at the top-left cell.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from random import Random

from .constants import (
    BASE_INTERVAL,
    COLS,
    FOOD_SCORE,
    MIN_INTERVAL,
    ROWS,
    SPEED_PER_POINT,
)

Point = tuple[int, int]
Direction = tuple[int, int]

RIGHT: Direction = (1, 0)
LEFT: Direction = (-1, 0)
UP: Direction = (0, -1)
DOWN: Direction = (0, 1)

DIRECTIONS: tuple[Direction, ...] = (LEFT, RIGHT, UP, DOWN)
OPPOSITE: dict[Direction, Direction] = {
    RIGHT: LEFT,
    LEFT: RIGHT,
    UP: DOWN,
    DOWN: UP,
}


@dataclass(frozen=True)
class SnakeState:
    cols: int = COLS
    rows: int = ROWS
    body: tuple[Point, ...] = ()          # head first, tail last
    direction: Direction = RIGHT
    pending: tuple[Direction, ...] = ()   # buffered turns, at most two
    food: Point | None = None
    score: int = 0
    alive: bool = True
    ticks: int = 0


def create_state(cols: int = COLS, rows: int = ROWS, rng: Random | None = None) -> SnakeState:
    """Build a fresh snake (length 3, moving right) with food on a free cell."""
    rng = rng or Random()
    cx, cy = cols // 2, rows // 2
    body = ((cx, cy), (cx - 1, cy), (cx - 2, cy))
    state = SnakeState(cols=cols, rows=rows, body=body, direction=RIGHT)
    return replace(state, food=random_empty_cell(state, rng))


def random_empty_cell(state: SnakeState, rng: Random) -> Point | None:
    """Uniformly pick a cell that is not part of the snake, or None if full."""
    occupied = set(state.body)
    free = [
        (x, y)
        for y in range(state.rows)
        for x in range(state.cols)
        if (x, y) not in occupied
    ]
    return rng.choice(free) if free else None


def queue_direction(state: SnakeState, direction: Direction) -> SnakeState:
    """Buffer a turn.

    Rejects instant 180-degree reversals (which would kill the player through
    their own neck) and duplicate inputs. Buffering two turns lets a quick
    "up then left" corner register inside a single grid tick.
    """
    if direction not in DIRECTIONS:
        return state
    last = state.pending[-1] if state.pending else state.direction
    if direction == last or direction == OPPOSITE[last]:
        return state
    if len(state.pending) >= 2:
        return state
    return replace(state, pending=state.pending + (direction,))


def step(state: SnakeState, rng: Random) -> SnakeState:
    """Advance one grid tick: move, eat, grow or die.

    Eating the tail cell is legal only on a non-eating move, because the tail
    vacates before the head arrives. That detail is covered by the tests.
    """
    if not state.alive:
        return state

    direction = state.pending[0] if state.pending else state.direction
    pending = state.pending[1:]
    head_x, head_y = state.body[0]
    head = (head_x + direction[0], head_y + direction[1])

    hit_wall = not (0 <= head[0] < state.cols and 0 <= head[1] < state.rows)
    eating = head == state.food
    hit_self = head in (state.body if eating else state.body[:-1])

    if hit_wall or hit_self:
        return replace(state, alive=False, direction=direction, pending=())

    body = (head,) + (state.body if eating else state.body[:-1])
    score = state.score + (FOOD_SCORE if eating else 0)

    nxt = replace(
        state,
        body=body,
        direction=direction,
        pending=pending,
        score=score,
        ticks=state.ticks + 1,
        food=None if eating else state.food,
    )
    if eating:
        nxt = replace(nxt, food=random_empty_cell(nxt, rng))
    return nxt


def interval_for(score: int) -> float:
    """Seconds per grid tick: the snake speeds up as the score grows."""
    return max(MIN_INTERVAL, BASE_INTERVAL - SPEED_PER_POINT * score)
