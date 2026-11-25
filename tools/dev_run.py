"""Run one game in a desktop pygame window.

This is the fast debugging loop: same scenes, same logic, but with a real
debugger, a real stack trace and no WebAssembly download.

    python tools/dev_run.py snake
    python tools/dev_run.py tictactoe
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import pygame  # noqa: E402

from arcade.actions import Action  # noqa: E402
from arcade.app import App  # noqa: E402
from arcade.storage import HighScores  # noqa: E402
from arcade.theme import Fonts  # noqa: E402

KEYMAP = {
    pygame.K_LEFT: Action.LEFT,
    pygame.K_a: Action.LEFT,
    pygame.K_RIGHT: Action.RIGHT,
    pygame.K_d: Action.RIGHT,
    pygame.K_UP: Action.UP,
    pygame.K_w: Action.UP,
    pygame.K_DOWN: Action.DOWN,
    pygame.K_s: Action.DOWN,
    pygame.K_SPACE: Action.ACTION,
    pygame.K_RETURN: Action.ACTION,
    pygame.K_p: Action.PAUSE,
    pygame.K_r: Action.RESTART,
    pygame.K_ESCAPE: Action.RESTART,
}


def main() -> None:
    slug = sys.argv[1] if len(sys.argv) > 1 else "snake"

    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((720, 720))
    pygame.display.set_caption(f"Arcade / Classic - {slug}")

    app = App(screen, Fonts(), HighScores())
    app.switch(slug)
    app.reset_scene()

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key in KEYMAP:
                app.input.push_action(KEYMAP[event.key])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                app.input.push_pointer(*event.pos)
        app.frame(dt)


if __name__ == "__main__":
    main()
