"""Entry point executed once inside Pyodide.

``src/loader.js`` imports this module, then calls the four functions below from
JavaScript: ``switch_game``, ``press``, ``pointer_down`` and ``arcade_frame``.

Only display + font are initialized, deliberately skipping the mixer: browsers
block audio until a user gesture, and neither game needs sound yet.
"""

from __future__ import annotations

import pygame
from js import localStorage

from arcade.app import App
from arcade.storage import HighScores
from arcade.theme import Fonts

SIZE = (720, 720)

pygame.display.init()
pygame.font.init()
pygame.display.set_caption("Arcade / Classic")
screen = pygame.display.set_mode(SIZE)

app = App(screen, Fonts(), HighScores(localStorage))


def switch_game(slug: str) -> None:
    """Select a game and start a fresh round (called by the Play button)."""
    app.switch(slug)
    app.reset_scene()


def press(action: str) -> None:
    """Queue a keyboard/touch action; consumed on the next frame."""
    app.input.push_action(action)


def pointer_down(x: float, y: float) -> None:
    """Queue a canvas tap in logical 720x720 coordinates."""
    app.input.push_pointer(int(x), int(y))


def arcade_frame(dt: float) -> None:
    """One browser animation frame. Called from requestAnimationFrame."""
    pygame.event.pump()  # keep SDL's queue healthy; input itself arrives via JS
    app.frame(float(dt))
