"""2048's pygame scene: key handling, tile rendering and the game-over card."""

from __future__ import annotations

import math
import random

import pygame

from arcade import theme
from arcade.actions import Action
from arcade.scene import BaseScene

from . import logic
from .constants import (
    BOARD_PADDING,
    BOARD_X,
    BOARD_Y,
    CELL,
    GAP,
    SIZE,
    TILE_RADIUS,
)

BEST_KEY = "2048.best"

TURNS = {
    Action.LEFT: logic.LEFT,
    Action.RIGHT: logic.RIGHT,
    Action.UP: logic.UP,
    Action.DOWN: logic.DOWN,
}

# Filled-tile colours grow brighter with the value; text flips to dark once the
# tile is light enough to need contrast.
TILE_STYLES: dict[int, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    2: ((30, 45, 68), theme.TEXT),
    4: ((38, 58, 86), theme.TEXT),
    8: ((20, 110, 140), theme.TEXT),
    16: ((24, 140, 150), theme.TEXT),
    32: ((52, 211, 153), theme.BG),
    64: ((250, 204, 21), theme.BG),
    128: ((251, 113, 133), theme.BG),
    256: ((244, 114, 182), theme.BG),
    512: ((192, 132, 252), theme.BG),
    1024: ((56, 189, 248), theme.BG),
    2048: ((255, 255, 255), theme.BG),
}
HIGH_TILE = ((52, 211, 153), theme.BG)


def build_scene(screen: pygame.Surface, fonts: theme.Fonts, scores) -> "Twenty48Scene":
    return Twenty48Scene(screen, fonts, scores)


class Twenty48Scene(BaseScene):
    slug = "twenty48"
    title = "2048"

    def __init__(self, screen: pygame.Surface, fonts: theme.Fonts, scores) -> None:
        super().__init__(screen, fonts, scores)
        self.rng = random.Random()
        self.reset()

    # --- setup -------------------------------------------------------------

    def reset(self) -> None:
        super().reset()
        self.state = logic.new_state(self.rng)
        self.best = int(self.scores.get(BEST_KEY, 0))
        self.new_best = False

    # --- input -------------------------------------------------------------

    def on_action(self, action: Action) -> None:
        direction = TURNS.get(action)
        if direction is not None:
            self._slide(direction)

    def _slide(self, direction: str) -> None:
        self.state = logic.slide(self.state, direction, self.rng)
        if self.state.over:
            self._end_round()

    # --- simulation --------------------------------------------------------

    def _end_round(self) -> None:
        if self.state.score > self.best:
            self.best = self.state.score
            self.scores.set(BEST_KEY, self.best)
            self.new_best = True
        self.finish()

    # --- rendering ---------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BG)

        theme.text(surface, self.fonts, "2048", "h2", theme.MINT, topleft=(BOARD_X, 28))
        theme.text(
            surface,
            self.fonts,
            f"SCORE {self.state.score}     BEST {self.best}",
            "small",
            theme.MUTED,
            topright=(self.width - BOARD_X, 40),
        )

        board_rect = (
            BOARD_X - BOARD_PADDING,
            BOARD_Y - BOARD_PADDING,
            SIZE * CELL + (SIZE - 1) * GAP + BOARD_PADDING * 2,
            SIZE * CELL + (SIZE - 1) * GAP + BOARD_PADDING * 2,
        )
        theme.panel(surface, board_rect, radius=18)

        for row in range(SIZE):
            for column in range(SIZE):
                value = self.state.board[row * SIZE + column]
                self._draw_tile(surface, column, row, value)

        if self.state.over:
            self._draw_game_over(surface)

    def _draw_tile(self, surface: pygame.Surface, column: int, row: int, value: int) -> None:
        rect = pygame.Rect(
            BOARD_X + column * (CELL + GAP),
            BOARD_Y + row * (CELL + GAP),
            CELL,
            CELL,
        )
        if value == 0:
            pygame.draw.rect(surface, theme.BOARD_ALT, rect, border_radius=TILE_RADIUS)
            return

        background, foreground = TILE_STYLES.get(value, HIGH_TILE)
        pygame.draw.rect(surface, background, rect, border_radius=TILE_RADIUS)

        if value < 100:
            style = "h2"
        elif value < 1000:
            style = "body"
        else:
            style = "small"
        theme.text(
            surface,
            self.fonts,
            value,
            style,
            foreground,
            center=rect.center,
        )

    def _draw_game_over(self, surface: pygame.Surface) -> None:
        theme.overlay(surface, 192)
        cx, cy = self.width // 2, self.height // 2

        theme.text(surface, self.fonts, "GAME OVER", "h1", theme.CORAL, center=(cx, cy - 92))
        theme.text(
            surface, self.fonts, f"SCORE {self.state.score}", "h2", theme.TEXT,
            center=(cx, cy - 22),
        )
        theme.text(
            surface, self.fonts, f"BEST {self.best}", "body", theme.MUTED,
            center=(cx, cy + 26),
        )
        if self.new_best:
            theme.text(
                surface, self.fonts, "NEW BEST", "small", theme.YELLOW,
                center=(cx, cy + 64),
            )

        alpha = 120 + int(105 * (0.5 + 0.5 * math.sin(self.time * 4.0)))
        theme.text(
            surface, self.fonts, "Press R or tap to play again", "small", theme.MUTED,
            center=(cx, cy + 124), alpha=alpha,
        )
