"""2048 rules: pure, deterministic, and independent of pygame.

The board is a 16-cell tuple in row-major order. Every move returns a new board
plus the points earned; a tile spawns only when something actually moved, which
is the rule that stops arrow-mashing from filling the board.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from random import Random

from .constants import SIZE, SPAWN_FOUR_CHANCE, TARGET

Board = tuple[int, ...]

LEFT = "left"
RIGHT = "right"
UP = "up"
DOWN = "down"
DIRECTIONS = (LEFT, RIGHT, UP, DOWN)


@dataclass(frozen=True)
class State:
    board: Board = (0,) * (SIZE * SIZE)
    score: int = 0
    over: bool = False
    ticks: int = 0


def new_state(rng: Random | None = None) -> State:
    """An empty board with the two starting tiles."""
    rng = rng or Random()
    board: Board = (0,) * (SIZE * SIZE)
    board = spawn_tile(board, rng)
    board = spawn_tile(board, rng)
    return State(board=board, over=not can_move(board))


def spawn_tile(board: Board, rng: Random) -> Board:
    """Put a 2 (or, rarely, a 4) in a uniformly random empty cell."""
    empty = [index for index, value in enumerate(board) if value == 0]
    if not empty:
        return board
    index = rng.choice(empty)
    value = 4 if rng.random() < SPAWN_FOUR_CHANCE else 2
    return board[:index] + (value,) + board[index + 1 :]


def can_move(board: Board) -> bool:
    """True while there is an empty cell or two equal neighbours."""
    for index, value in enumerate(board):
        if value == 0:
            return True
        column, row = index % SIZE, index // SIZE
        if column + 1 < SIZE and board[index + 1] == value:
            return True
        if row + 1 < SIZE and board[index + SIZE] == value:
            return True
    return False


def max_tile(board: Board) -> int:
    return max(board)


def move(board: Board, direction: str) -> tuple[Board, int, bool]:
    """Slide and merge every line once.

    Returns ``(new_board, points, changed)``. Merges never chain: on a line
    ``(2, 2, 2, 2)`` the result is ``(4, 4, 0, 0)``, not ``(8, 0, 0, 0)``.
    """
    if direction not in DIRECTIONS:
        return board, 0, False

    rows = _rows(board)
    if direction == RIGHT:
        rows = [list(reversed(row)) for row in rows]
    elif direction in (UP, DOWN):
        rows = _transpose(rows)
        if direction == DOWN:
            rows = [list(reversed(row)) for row in rows]

    points = 0
    changed = False
    merged_rows: list[list[int]] = []
    for row in rows:
        line, gained, moved = _slide_line(row)
        points += gained
        changed = changed or moved
        merged_rows.append(line)

    if direction == RIGHT:
        merged_rows = [list(reversed(row)) for row in merged_rows]
    elif direction in (UP, DOWN):
        if direction == DOWN:
            merged_rows = [list(reversed(row)) for row in merged_rows]
        merged_rows = _transpose(merged_rows)

    return _flatten(merged_rows), points, changed


def slide(state: State, direction: str, rng: Random) -> State:
    """A player move: merge, score, then spawn one new tile if anything moved."""
    if state.over:
        return state

    board, points, changed = move(state.board, direction)
    if not changed:
        return state

    board = spawn_tile(board, rng)
    return replace(
        state,
        board=board,
        score=state.score + points,
        over=not can_move(board),
        ticks=state.ticks + 1,
    )


# --- line helpers -----------------------------------------------------------


def _slide_line(line: list[int]) -> tuple[list[int], int, bool]:
    """Slide one line to the left, merging equal neighbours once."""
    values = [value for value in line if value]
    merged: list[int] = []
    points = 0
    index = 0
    while index < len(values):
        if index + 1 < len(values) and values[index] == values[index + 1]:
            value = values[index] * 2
            merged.append(value)
            points += value
            index += 2
        else:
            merged.append(values[index])
            index += 1

    merged += [0] * (SIZE - len(merged))
    return merged, points, merged != line


def _rows(board: Board) -> list[list[int]]:
    return [list(board[row * SIZE : (row + 1) * SIZE]) for row in range(SIZE)]


def _flatten(rows: list[list[int]]) -> Board:
    return tuple(value for row in rows for value in row)


def _transpose(rows: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*rows)]


def reached_target(board: Board) -> bool:
    return max_tile(board) >= TARGET
