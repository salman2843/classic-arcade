"""Headless smoke tests for the engine and the pygame scenes.

SDL runs with the dummy video/audio drivers, so this exercises every draw call
and the real input pipeline without opening a window. It catches the boring
breakages (bad rect, missing attribute) that WebAssembly would otherwise hide
behind a 12 MB download.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

pygame = pytest.importorskip("pygame")

from arcade.actions import Action
from arcade.storage import HighScores
from arcade.theme import Fonts
from games.tictactoe import logic as ttt
from games.tictactoe.constants import BOARD_X, BOARD_Y, CELL
from games.tictactoe.scene import build_scene as build_ttt
from games.snake.scene import build_scene as build_snake


@pytest.fixture(scope="module")
def screen():
    pygame.display.init()
    pygame.font.init()
    surface = pygame.display.set_mode((720, 720))
    yield surface
    pygame.display.quit()


@pytest.fixture(scope="module")
def fonts(screen):
    return Fonts()


def cell_center(index: int) -> tuple[int, int]:
    column, row = index % 3, index // 3
    return (
        BOARD_X + column * CELL + CELL // 2,
        BOARD_Y + row * CELL + CELL // 2,
    )


def test_snake_runs_into_the_wall_and_can_restart(screen, fonts):
    scene = build_snake(screen, fonts, HighScores())

    for _ in range(400):
        scene.update(0.13)
        scene.draw(screen)
        if scene.finished:
            break

    assert scene.finished
    assert not scene.state.alive

    scene.update(0.6)  # let the tap-to-restart grace period pass
    scene.pointer_down(360, 360)
    assert not scene.finished
    assert scene.state.alive

    scene.handle_action(Action.PAUSE)
    ticks = scene.state.ticks
    scene.update(2.0)
    assert scene.state.ticks == ticks
    scene.draw(screen)

    scene.handle_action(Action.PAUSE)
    scene.handle_action(Action.RESTART)
    assert scene.state.ticks == 0


def test_snake_turns_are_buffered_through_the_action_pipeline(screen, fonts):
    scene = build_snake(screen, fonts, HighScores())
    scene.handle_action(Action.UP)
    scene.update(0.2)

    assert scene.state.direction == (0, -1)


def test_tictactoe_plays_a_full_round(screen, fonts):
    scene = build_ttt(screen, fonts, HighScores())
    scene.draw(screen)

    scene.pointer_down(*cell_center(4))
    assert scene.board[4] == ttt.X
    assert scene.turn == ttt.O

    for _ in range(40):
        scene.update(0.02)
    assert sum(1 for cell in scene.board if cell != ttt.EMPTY) == 2
    scene.draw(screen)

    # Clicking a taken square is ignored.
    before = scene.board
    scene.pointer_down(*cell_center(4))
    assert scene.board == before

    for _ in range(9):
        if scene.result is not None:
            break
        index = next(i for i, cell in enumerate(scene.board) if cell == ttt.EMPTY)
        scene.pointer_down(*cell_center(index))
        for _ in range(40):
            scene.update(0.02)

    assert scene.result is not None
    assert ttt.winner(scene.board) == scene.result
    scene.draw(screen)

    scene.handle_action(Action.RESTART)
    assert scene.board == ttt.new_board()
    assert scene.result is None
