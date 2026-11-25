"""Scene contract shared by every game.

A scene owns one play session. The engine (``App``) feeds it actions, one dt per
frame, and asks it to draw. Games only implement the small hooks at the bottom;
pause, restart and "tap to play again" behavior come from this base class.
"""

from __future__ import annotations

import pygame

from . import theme
from .actions import Action

RESTART_GRACE = 0.55  # seconds after game over before a tap can restart


class BaseScene:
    slug: str = ""
    title: str = ""

    def __init__(self, screen: pygame.Surface, fonts: theme.Fonts, scores) -> None:
        self.screen = screen
        self.fonts = fonts
        self.scores = scores
        self.width, self.height = screen.get_size()
        self.time = 0.0
        self.paused = False
        self.finished = False
        self._finished_at = -99.0

    # --- lifecycle ---------------------------------------------------------

    def reset(self) -> None:
        """Start a fresh round. Subclasses extend this and call super().reset()."""
        self.paused = False
        self.finished = False
        self._finished_at = -99.0

    def finish(self) -> None:
        """Mark the round as over and start the tap-to-restart cooldown."""
        self.finished = True
        self._finished_at = self.time

    # --- input -------------------------------------------------------------

    def handle_action(self, action: Action) -> None:
        """Global keys first (pause/restart), then the game's own handler."""
        if action is Action.PAUSE:
            if not self.finished:
                self.paused = not self.paused
            return
        if action is Action.RESTART:
            self.reset()
            return
        if action is Action.ACTION and self.finished:
            self.reset()
            return
        if self.paused or self.finished:
            return
        self.on_action(action)

    def pointer_down(self, x: int, y: int) -> None:
        """Canvas taps with logical 720x720 coordinates."""
        if self.paused:
            return
        if self.finished:
            if self.time - self._finished_at >= RESTART_GRACE:
                self.reset()
            return
        self.on_pointer(x, y)

    # --- frame -------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.paused:
            return
        self.time += dt
        self.tick(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.render(surface)
        if self.paused:
            theme.overlay(surface, 170)
            theme.text(
                surface, self.fonts, "PAUSED", "h1", theme.TEXT,
                center=(self.width // 2, self.height // 2 - 16),
            )
            theme.text(
                surface, self.fonts, "Press P to resume", "body", theme.MUTED,
                center=(self.width // 2, self.height // 2 + 38),
            )

    # --- hooks for games ---------------------------------------------------

    def on_action(self, action: Action) -> None:
        """A game key (left/right/action…) arrived while the round is live."""

    def on_pointer(self, x: int, y: int) -> None:
        """The player tapped the canvas at (x, y)."""

    def tick(self, dt: float) -> None:
        """Advance the simulation by dt seconds (render rate, not fixed step)."""

    def render(self, surface: pygame.Surface) -> None:
        raise NotImplementedError
