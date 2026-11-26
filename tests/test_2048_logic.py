"""2048 rules: slides, merges, scoring, spawning and game over."""

from random import Random

import pytest

from games.twenty48 import logic
from games.twenty48.constants import SIZE, TARGET


def board(*rows: tuple[int, ...]) -> logic.Board:
    return tuple(value for row in rows for value in row)


def test_new_state_has_two_tiles_and_is_not_over():
    a = logic.new_state(Random(7))
    b = logic.new_state(Random(7))

    assert a == b
    assert sum(1 for value in a.board if value) == 2
    assert not a.over
    assert a.score == 0


def test_move_left_merges_pairs_once():
    started = board(
        (2, 2, 2, 2),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
    )

    moved, points, changed = logic.move(started, logic.LEFT)

    assert changed
    assert points == 8
    assert moved[:4] == (4, 4, 0, 0)


def test_merges_do_not_chain():
    started = board(
        (4, 4, 8, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
    )

    moved, points, _ = logic.move(started, logic.LEFT)

    assert moved[:4] == (8, 8, 0, 0)
    assert points == 8


def test_move_right_slides_toward_the_right_edge():
    started = board(
        (2, 0, 2, 4),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
    )

    moved, points, _ = logic.move(started, logic.RIGHT)

    assert moved[:4] == (0, 0, 4, 4)
    assert points == 4


def test_move_up_and_down_work_on_columns():
    started = board(
        (2, 0, 0, 0),
        (2, 0, 0, 0),
        (4, 0, 0, 0),
        (0, 0, 0, 0),
    )

    up, up_points, _ = logic.move(started, logic.UP)
    assert up[:4] == (4, 0, 0, 0)
    assert up[4:8] == (4, 0, 0, 0)
    assert up_points == 4

    down, down_points, _ = logic.move(started, logic.DOWN)
    assert down[8] == 4
    assert down[12] == 4
    assert down[4] == 0
    assert down_points == 4


def test_move_that_changes_nothing_reports_no_change():
    started = board(
        (2, 4, 2, 4),
        (4, 2, 4, 2),
        (2, 4, 2, 4),
        (4, 2, 4, 2),
    )

    moved, points, changed = logic.move(started, logic.LEFT)

    assert moved == started
    assert points == 0
    assert not changed


def test_slide_spawns_exactly_one_tile_and_scores():
    state = logic.State(board=board(
        (2, 2, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
    ))

    after = logic.slide(state, logic.LEFT, Random(3))

    assert after.score == 4
    assert after.ticks == 1
    assert sum(1 for value in after.board if value) == 2  # the merged 4 + one spawn
    assert after.board[0] == 4
    assert 2 in after.board or 4 in after.board


def test_slide_without_movement_does_not_spawn_or_score():
    state = logic.State(board=board(
        (2, 4, 2, 4),
        (4, 2, 4, 2),
        (2, 4, 2, 4),
        (4, 2, 4, 2),
    ))

    after = logic.slide(state, logic.LEFT, Random(3))

    assert after == state


def test_spawning_is_seeded():
    state = logic.State(board=board(
        (2, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
    ))

    a = logic.slide(state, logic.RIGHT, Random(11))
    b = logic.slide(state, logic.RIGHT, Random(11))

    assert a == b
    assert a.board[3] == 2


def test_can_move_detects_empty_cells_and_equal_neighbours():
    full = board(
        (2, 4, 2, 4),
        (4, 2, 4, 2),
        (2, 4, 2, 4),
        (4, 2, 4, 2),
    )
    assert not logic.can_move(full)

    with_hole = full[:15] + (0,)
    assert logic.can_move(with_hole)

    with_pair = board(
        (2, 4, 2, 4),
        (4, 2, 4, 2),
        (2, 4, 2, 4),
        (4, 2, 2, 4),
    )
    assert logic.can_move(with_pair)


def test_slide_keeps_the_over_flag_consistent_with_the_board():
    state = logic.State(board=board(
        (2, 4, 2, 4),
        (4, 2, 4, 2),
        (2, 4, 2, 4),
        (4, 2, 4, 0),
    ))

    after = logic.slide(state, logic.RIGHT, Random(5))

    assert after.over == (not logic.can_move(after.board))
    assert sum(1 for value in after.board if value) == 16


def test_over_state_ignores_input():
    state = logic.State(board=(2,) * (SIZE * SIZE), over=True, score=99)

    assert logic.slide(state, logic.LEFT, Random(1)) is state


def test_reached_target():
    assert not logic.reached_target((2, 4) + (0,) * 14)
    assert logic.reached_target((2, TARGET) + (0,) * 14)


def test_unknown_direction_is_ignored():
    started = board(
        (2, 2, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
    )

    assert logic.move(started, "sideways") == (started, 0, False)
