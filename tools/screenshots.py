"""Render showcase screenshots headlessly (also a visual smoke test).

    python tools/screenshots.py

Writes screenshots/snake.png and screenshots/tictactoe.png. The scenes are real,
only the state is curated so the boards do not look empty.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
OUT = ROOT / "screenshots"

import pygame  # noqa: E402

from arcade.storage import HighScores  # noqa: E402
from arcade.theme import Fonts  # noqa: E402
from games.snake import logic as snake_logic  # noqa: E402
from games.snake.scene import build_scene as build_snake  # noqa: E402
from games.tictactoe import logic as ttt  # noqa: E402
from games.tictactoe.scene import build_scene as build_ttt  # noqa: E402


def tictactoe_shot(fonts: Fonts) -> pygame.Surface:
    surface = pygame.Surface((720, 720))
    scene = build_ttt(surface, fonts, HighScores())

    # A completed diagonal win for X, with believable counters.
    scene.board = (
        ttt.X, ttt.O, ttt.X,
        ttt.O, ttt.X, ttt.O,
        ttt.O, ttt.X, ttt.X,
    )
    scene.result = ttt.X
    scene.win_line = (0, 4, 8)
    scene.wins, scene.losses, scene.draws = 4, 1, 2
    scene.finished = True
    scene._finished_at = scene.time
    scene.time = 0.42  # part-way through the pulsing hint

    scene.draw(surface)
    return surface


def snake_shot(fonts: Fonts) -> pygame.Surface:
    surface = pygame.Surface((720, 720))
    scene = build_snake(surface, fonts, HighScores())

    scene.state = snake_logic.SnakeState(
        body=(
            (0, 11), (21, 11), (20, 11), (19, 11), (18, 11), (17, 11),
            (16, 11), (16, 12), (16, 13), (17, 13), (18, 13), (19, 13),
        ),
        direction=snake_logic.RIGHT,
        food=(5, 7),
        score=90,
    )
    # Halfway through the tick that crossed the right seam: the head is drawn
    # leaving on the right and arriving on the left at the same time.
    scene._prev_body = scene.state.body[1:] + (scene.state.body[-1],)
    scene.timer.reset()
    scene.timer._accumulator = snake_logic.interval_for(scene.state.score) * 0.45
    scene.best = 120
    scene.time = 0.3

    scene.draw(surface)
    return surface


def main() -> None:
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((720, 720))
    fonts = Fonts()

    OUT.mkdir(exist_ok=True)
    pygame.image.save(tictactoe_shot(fonts), OUT / "tictactoe.png")
    pygame.image.save(snake_shot(fonts), OUT / "snake.png")
    pygame.display.quit()
    print(f"wrote {OUT / 'tictactoe.png'}")
    print(f"wrote {OUT / 'snake.png'}")


if __name__ == "__main__":
    main()
