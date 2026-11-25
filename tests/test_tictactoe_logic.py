"""Tic-Tac-Toe rules: transitions and outcome detection."""

import pytest

from games.tictactoe.logic import (
    DRAW,
    EMPTY,
    O,
    X,
    apply_move,
    is_over,
    legal_moves,
    new_board,
    other,
    winning_line,
    winner,
)


def board(rows: str) -> tuple[int, ...]:
    """Build a board from three strings: '.' empty, 'X', 'O'."""
    cells = []
    for char in rows.replace(" ", ""):
        cells.append({"X": X, "O": O, ".": EMPTY}[char])
    assert len(cells) == 9
    return tuple(cells)


def test_new_board_is_empty():
    assert new_board() == (EMPTY,) * 9
    assert legal_moves(new_board()) == list(range(9))
    assert winner(new_board()) is None
    assert not is_over(new_board())


def test_apply_move_is_immutable_and_validates():
    before = new_board()
    after = apply_move(before, 4, X)

    assert before == new_board()
    assert after[4] == X

    with pytest.raises(ValueError):
        apply_move(after, 4, O)
    with pytest.raises(ValueError):
        apply_move(before, 9, X)


def test_rows_columns_and_diagonals_win():
    row = board("XXX" "OO." "...")
    column = board("X.O" "X.O" "X..")
    diagonal = board("X.O" ".X." "O.X")
    anti = board("O.X" ".O." "X.O")

    assert winner(row) == X
    assert winner(column) == X
    assert winner(diagonal) == X
    assert winner(anti) == O


def test_winning_line_points_at_the_three_cells():
    assert winning_line(board("O.X" "O.X" "O..")) == (0, 3, 6)
    assert winning_line(new_board()) is None


def test_full_board_without_a_line_is_a_draw():
    full = board("XOX" "XOO" "OXX")

    assert winner(full) == DRAW
    assert is_over(full)
    assert legal_moves(full) == []


def test_other_swaps_players():
    assert other(X) == O
    assert other(O) == X
