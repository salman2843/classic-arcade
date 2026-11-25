"""The Tic-Tac-Toe opponent must be provably hard to beat."""

from random import Random

from games.tictactoe.ai import best_move, choose_move, position_value
from games.tictactoe.logic import (
    DRAW,
    EMPTY,
    O,
    X,
    apply_move,
    legal_moves,
    new_board,
    other,
    winner,
)


def board(rows: str) -> tuple[int, ...]:
    cells = []
    for char in rows.replace(" ", ""):
        cells.append({"X": X, "O": O, ".": EMPTY}[char])
    assert len(cells) == 9
    return tuple(cells)


def play_out(ai_player: int, seed: int, opponent: str = "random") -> int:
    """Play one game, AI on one side, random (or perfect) on the other."""
    rng = Random(seed)
    current = new_board()
    turn = X
    while (outcome := winner(current)) is None:
        if turn == ai_player:
            move = best_move(current, turn)
        elif opponent == "perfect":
            move = best_move(current, turn)
        else:
            move = rng.choice(legal_moves(current))
        current = apply_move(current, move, turn)
        turn = other(turn)
    return outcome


def test_perfect_play_from_empty_board_is_a_draw():
    assert position_value(new_board(), X) == 0


def test_first_move_is_center_or_corner():
    move = best_move(new_board(), X)
    assert move in {0, 2, 4, 6, 8}


def test_ai_takes_an_immediate_win():
    # O can complete 3-4-5; X also threatens 0-1-2, but winning comes first.
    current = board("XX." "OO." "X..")
    assert best_move(current, O) == 5


def test_ai_blocks_an_immediate_loss():
    # X threatens 0-1-2. O has no win and no better fork, so 2 is forced.
    current = board("XX." "..O" "X.O")
    assert best_move(current, O) == 2


def test_ai_never_loses_to_random_as_x():
    for seed in range(60):
        assert play_out(X, seed, "random") in {X, DRAW}


def test_ai_never_loses_to_random_as_o():
    for seed in range(60):
        assert play_out(O, seed, "random") in {O, DRAW}


def test_ai_draws_itself():
    assert play_out(X, 1, "perfect") == DRAW


def test_easy_difficulty_still_returns_legal_moves():
    rng = Random(5)
    current = new_board()
    for _ in range(9):
        move = choose_move(current, X, rng, difficulty="easy")
        assert move in legal_moves(current)
        current = apply_move(current, move, X)
