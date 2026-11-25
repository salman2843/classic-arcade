"""Application shell: one screen, one active scene, one frame at a time."""

from __future__ import annotations

import importlib

import pygame

from . import theme
from .input import InputQueue
from .scene import BaseScene


class App:
    def __init__(self, screen: pygame.Surface, fonts: theme.Fonts, scores) -> None:
        self.screen = screen
        self.fonts = fonts
        self.scores = scores
        self.input = InputQueue()
        self.scene: BaseScene | None = None
        self.slug: str | None = None

    def switch(self, slug: str) -> None:
        """Load a game module lazily and replace the active scene.

        The SDL canvas and the pygame modules stay initialized; only the Python
        object changes. That is what makes switching games instant.
        """
        if not slug or slug == self.slug:
            return
        module = importlib.import_module(f"games.{slug}.scene")
        self.scene = module.build_scene(self.screen, self.fonts, self.scores)
        self.slug = slug
        self.input.clear()

    def reset_scene(self) -> None:
        """Begin a fresh round, used every time Play is pressed."""
        if self.scene is not None:
            self.scene.reset()
            self.input.clear()

    def frame(self, dt: float) -> None:
        """One rendered frame: drain input, simulate, draw, present."""
        if self.scene is None:
            self.screen.fill(theme.BG)
            pygame.display.flip()
            return

        for action in self.input.drain_actions():
            self.scene.handle_action(action)
        for x, y in self.input.drain_pointers():
            self.scene.pointer_down(x, y)

        self.scene.update(dt)
        self.scene.draw(self.screen)
        pygame.display.flip()
