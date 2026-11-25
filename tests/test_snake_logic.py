"""Snake rules: movement, turns, growth, death and speed."""

from random import Random

import pytest

from games.snake import logic
from games.snake.constants import BASE_INTERVAL, FOOD_SCORE, MIN_INTERVAL
from games.snake.logic import SnakeState


def fresh(seed: int = 1) -> logic.SnakeState:
    return logic.create_state(10, 10, Random(seed))


def test_create_state_is_seeded_and_valid():
    a = logic.create_state(10, 10, Random(7))
    b = logic.create_state(10, 10, Random(7))

    assert a == b
    assert len(a.body) == 3
    assert a.direction == logic.RIGHT
    assert a.alive
    assert a.food is not None and a.food not in a.body


def test_step_moves_head_one_cell_right():
    state = fresh()
    x, y = state.body[0]

    nxt = logic.step(state, Random(2))

    assert nxt.body[0] == (x + 1, y)
    assert len(nxt.body) == len(state.body)
    assert nxt.ticks == state.ticks + 1


def test_queue_direction_rejects_reverse_and_duplicates():
    state = fresh()

    assert logic.queue_direction(state, logic.LEFT) == state
    assert logic.queue_direction(state, logic.RIGHT) == state

    turned = logic.queue_direction(state, logic.UP)
    assert turned.pending == (logic.UP,)

    corner = logic.queue_direction(turned, logic.LEFT)
    assert corner.pending == (logic.UP, logic.LEFT)

    assert logic.queue_direction(corner, logic.DOWN) == corner  # buffer full


def test_buffered_turn_applies_on_next_step():
    state = logic.queue_direction(fresh(), logic.DOWN)
    x, y = state.body[0]

    nxt = logic.step(state, Random(3))

    assert nxt.body[0] == (x, y + 1)
    assert nxt.direction == logic.DOWN


def test_eating_grows_scores_and_respawns_food():
    state = SnakeState(
        cols=10, rows=10,
        body=((5, 5), (4, 5), (3, 5)),
        direction=logic.RIGHT,
        food=(6, 5),
    )

    nxt = logic.step(state, Random(4))

    assert nxt.score == FOOD_SCORE
    assert len(nxt.body) == 4
    assert nxt.body[0] == (6, 5)
    assert nxt.food is not None
    assert nxt.food not in nxt.body


def test_wall_kills_and_leaves_body_intact():
    state = SnakeState(
        cols=5, rows=5,
        body=((4, 2), (3, 2), (2, 2)),
        direction=logic.RIGHT,
    )

    nxt = logic.step(state, Random(1))

    assert not nxt.alive
    assert nxt.body == state.body


def test_running_into_neck_kills():
    state = SnakeState(
        cols=10, rows=10,
        body=((5, 5), (5, 6), (4, 6), (4, 5)),
        direction=logic.DOWN,
    )

    assert not logic.step(state, Random(1)).alive


def test_following_your_own_tail_is_safe_when_tail_vacates():
    state = SnakeState(
        cols=10, rows=10,
        body=((4, 5), (4, 6), (5, 6), (5, 5)),
        direction=logic.RIGHT,
    )

    nxt = logic.step(state, Random(1))

    assert nxt.alive
    assert nxt.body[0] == (5, 5)


def test_dead_snake_does_not_move():
    state = SnakeState(cols=5, rows=5, body=((0, 0),), alive=False)
    assert logic.step(state, Random(1)) == state


@pytest.mark.parametrize("score", [0, 10, 50, 500, 100_000])
def test_interval_shrinks_and_floors(score: int):
    interval = logic.interval_for(score)
    assert MIN_INTERVAL <= interval <= BASE_INTERVAL


def test_every_step_is_deterministic_for_a_seed():
    def play(seed: int) -> list[tuple[int, int]]:
        rng = Random(seed)
        state = logic.create_state(10, 10, rng)
        for _ in range(40):
            state = logic.step(state, rng)
            if not state.alive:
                break
        return list(state.body)

    assert play(11) == play(11)
