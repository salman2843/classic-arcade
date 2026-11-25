"""Tests for the small shared engine pieces."""

from arcade.actions import Action
from arcade.input import MAX_ACTIONS, InputQueue
from arcade.storage import HighScores
from arcade.timing import FixedStep


class FakeStorage:
    def __init__(self):
        self.data = {}

    def getItem(self, key):
        return self.data.get(key)

    def setItem(self, key, value):
        self.data[key] = value


def test_fixed_step_converts_time_to_whole_ticks():
    step = FixedStep()
    assert step.advance(0.02, 0.05) == 0  # not enough time for a tick
    assert step.advance(0.04, 0.05) == 1  # 0.06 accumulated, one tick due
    assert step.advance(0.12, 0.05) == 2  # 0.13 accumulated, two ticks due


def test_fixed_step_clamps_long_frames():
    step = FixedStep(max_frame=0.25, max_steps=8)
    # 10 seconds would be 100 ticks; the clamp limits it to 0.25s -> 2 ticks.
    assert step.advance(10.0, 0.1) == 2


def test_input_queue_accepts_strings_and_ignores_junk():
    queue = InputQueue()
    queue.push_action("left")
    queue.push_action(Action.PAUSE)
    queue.push_action("not-an-action")
    queue.push_pointer(10.7, 20.2)

    assert queue.drain_actions() == [Action.LEFT, Action.PAUSE]
    assert queue.drain_pointers() == [(10, 20)]
    assert queue.drain_actions() == []


def test_input_queue_is_bounded():
    queue = InputQueue()
    for _ in range(MAX_ACTIONS * 3):
        queue.push_action("left")
    assert len(queue.drain_actions()) == MAX_ACTIONS


def test_high_scores_round_trip_through_a_backend():
    backend = FakeStorage()

    scores = HighScores(backend)
    scores.set("snake.best", 120)
    scores.set("ttt.wins", 3)

    reloaded = HighScores(backend)
    assert reloaded.get("snake.best") == 120
    assert reloaded.get("ttt.wins") == 3
    assert reloaded.get("missing", 0) == 0


def test_high_scores_without_a_backend_still_work():
    scores = HighScores()
    scores.set("snake.best", 40)
    assert scores.get("snake.best") == 40
