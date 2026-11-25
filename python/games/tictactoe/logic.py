"""Tic-Tac-Toe rules: board representation, legality and win detection.

A board is a 9-tuple in row-major order. Empty cells are ``EMPTY`` (0), players
are ``X`` (1) and ``O`` (2). ``winner`` returns ``DRAW`` (3) for a full board and
``None`` while the game is still running.
"""

from __future__ import annotations

EMPTY = 0
X = 1
O = 2
DRAW = 3

Board = tuple[int, ...]

# Rows, columns, then the two diagonals.
LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

CENTER = 4
CORNERS = frozenset({0, 2, 6, 8})


def new_board() -> Board:
    return (EMPTY,) * 9


def other(player: int) -> int:
    return O if player == X else X


def legal_moves(board: Board) -> list[int]:
    return [index for index, cell in enumerate(board) if cell == EMPTY]


def apply_move(board: Board, index: int, player: int) -> Board:
    """Return a new board with ``player`` placed at ``index``."""
    if not 0 <= index < 9:
        raise ValueError(f"cell {index} is outside the board")
    if board[index] != EMPTY:
        raise ValueError(f"cell {index} is already taken")
    return board[:index] + (player,) + board[index + 1 :]


def winning_line(board: Board) -> tuple[int, int, int] | None:
    """The three cells that make a line, or None."""
    for line in LINES:
        a, b, c = line
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return line
    return None


def winner(board: Board) -> int | None:
    """X, O, DRAW when the game is over; None while it is still running."""
    line = winning_line(board)
    if line is not None:
        return board[line[0]]
    if EMPTY not in board:
        return DRAW
    return None


def is_over(board: Board) -> bool:
    return winner(board) is not None
