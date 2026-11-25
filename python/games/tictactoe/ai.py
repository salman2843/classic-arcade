"""Tic-Tac-Toe opponent.

``position_value`` is a memoized negamax search over the remaining empty cells.
A 3x3 board has at most 9! = 362,880 move orders but only 5,478 distinct
positions, so caching makes the whole game tree effectively instant.
"""

from __future__ import annotations

from functools import lru_cache
from random import Random

from .logic import (
    CENTER,
    CORNERS,
    DRAW,
    Board,
    apply_move,
    legal_moves,
    other,
    winner,
)


@lru_cache(maxsize=None)
def position_value(board: Board, player: int) -> int:
    """Value of ``board`` for the player to move: +1 win, 0 draw, -1 loss.

    Perfect play is assumed for both sides, which is exactly what makes this a
    reliable test oracle ("the AI must never score below 0").
    """
    outcome = winner(board)
    if outcome is not None:
        if outcome == DRAW:
            return 0
        return 1 if outcome == player else -1

    best = -2
    for index in legal_moves(board):
        reply = apply_move(board, index, player)
        best = max(best, -position_value(reply, other(player)))
    return best


def _preference(index: int) -> int:
    """Tie-breaker so equal moves pick center, then corners, then edges."""
    if index == CENTER:
        return 2
    if index in CORNERS:
        return 1
    return 0


def best_move(board: Board, player: int) -> int | None:
    """The highest-value move for ``player``, or None on a finished board."""
    moves = legal_moves(board)
    if not moves:
        return None

    def score(index: int) -> tuple[int, int]:
        reply = apply_move(board, index, player)
        # position_value is from the opponent's point of view, so negate it.
        return (-position_value(reply, other(player)), _preference(index))

    return max(moves, key=score)


def choose_move(
    board: Board,
    player: int,
    rng: Random | None = None,
    difficulty: str = "hard",
) -> int | None:
    """Pick a move, optionally blundering on purpose.

    easy:   uniformly random.
    medium: random 35% of the time, otherwise perfect.
    hard:   perfect play (the default used by the scene).
    """
    rng = rng or Random()
    moves = legal_moves(board)
    if not moves:
        return None
    if difficulty == "easy":
        return rng.choice(moves)
    if difficulty == "medium" and rng.random() < 0.35:
        return rng.choice(moves)
    return best_move(board, player)
