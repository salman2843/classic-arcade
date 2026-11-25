"""Snake's pygame scene: input mapping, timing and rendering.

Rules live in ``logic.py``; this file is allowed to touch pygame and the screen.
The only state here is presentation state (best score, timers, cached board art).
"""

from __future__ import annotations

import math
import random

import pygame

from arcade import theme
from arcade.actions import Action
from arcade.scene import BaseScene
from arcade.timing import FixedStep

from . import logic
from .constants import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    BOARD_X,
    BOARD_Y,
    CELL,
    FOOD_RADIUS,
    ROWS,
    COLS,
    SEGMENT_INSET,
    SEGMENT_RADIUS,
)

BEST_KEY = "snake.best"


def build_scene(screen: pygame.Surface, fonts: theme.Fonts, scores) -> "SnakeScene":
    return SnakeScene(screen, fonts, scores)


class SnakeScene(BaseScene):
    slug = "snake"
    title = "Snake"

    def __init__(self, screen: pygame.Surface, fonts: theme.Fonts, scores) -> None:
        super().__init__(screen, fonts, scores)
        self.rng = random.Random()
        self.timer = FixedStep()
        # Checkerboard is static, so render it once instead of 484 rects a frame.
        self._board_art = self._build_board_art()
        self.reset()

    # --- setup -------------------------------------------------------------

    def _build_board_art(self) -> pygame.Surface:
        art = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        art.fill(theme.BOARD)
        for y in range(ROWS):
            for x in range(COLS):
                if (x + y) % 2 == 0:
                    pygame.draw.rect(art, theme.BOARD_ALT, (x * CELL, y * CELL, CELL, CELL))
        return art

    def reset(self) -> None:
        super().reset()
        self.state = logic.create_state(rng=self.rng)
        self.timer.reset()
        self.best = int(self.scores.get(BEST_KEY, 0))
        self.new_best = False

    # --- input -------------------------------------------------------------

    def on_action(self, action: Action) -> None:
        turns = {
            Action.LEFT: logic.LEFT,
            Action.RIGHT: logic.RIGHT,
            Action.UP: logic.UP,
            Action.DOWN: logic.DOWN,
        }
        direction = turns.get(action)
        if direction is not None:
            self.state = logic.queue_direction(self.state, direction)

    # --- simulation --------------------------------------------------------

    def tick(self, dt: float) -> None:
        if not self.state.alive:
            return

        interval = logic.interval_for(self.state.score)
        for _ in range(self.timer.advance(dt, interval)):
            self.state = logic.step(self.state, self.rng)
            if not self.state.alive:
                self._end_round()
                break

    def _end_round(self) -> None:
        if self.state.score > self.best:
            self.best = self.state.score
            self.scores.set(BEST_KEY, self.best)
            self.new_best = True
        self.finish()

    # --- rendering ---------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BG)
        self._draw_hud(surface)

        surface.blit(self._board_art, (BOARD_X, BOARD_Y))
        pygame.draw.rect(
            surface,
            theme.LINE,
            (BOARD_X - 4, BOARD_Y - 4, BOARD_WIDTH + 8, BOARD_HEIGHT + 8),
            width=2,
            border_radius=12,
        )

        self._draw_food(surface)
        self._draw_snake(surface)

        if not self.state.alive:
            self._draw_game_over(surface)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        theme.text(surface, self.fonts, "SNAKE", "h2", theme.MINT, topleft=(BOARD_X, 22))
        theme.text(
            surface,
            self.fonts,
            f"SCORE {self.state.score}     BEST {self.best}",
            "small",
            theme.MUTED,
            topright=(self.width - BOARD_X, 32),
        )

    def _draw_food(self, surface: pygame.Surface) -> None:
        food = self.state.food
        if food is None:
            return
        pulse = math.sin(self.time * 7.0) * 2.0
        center = (
            BOARD_X + food[0] * CELL + CELL // 2,
            BOARD_Y + food[1] * CELL + CELL // 2,
        )
        pygame.draw.circle(surface, (68, 26, 40), center, int(FOOD_RADIUS + 7 + pulse))
        pygame.draw.circle(surface, theme.CORAL, center, int(FOOD_RADIUS + pulse))
        pygame.draw.circle(surface, (255, 214, 222), (center[0] - 2, center[1] - 2), 3)

    def _draw_snake(self, surface: pygame.Surface) -> None:
        body = self.state.body
        count = len(body)
        for index in range(count - 1, -1, -1):
            x, y = body[index]
            t = 1.0 if count == 1 else (count - 1 - index) / (count - 1)
            color = theme.lerp_color(theme.MINT_DARK, theme.MINT, t)
            rect = pygame.Rect(
                BOARD_X + x * CELL + SEGMENT_INSET,
                BOARD_Y + y * CELL + SEGMENT_INSET,
                CELL - SEGMENT_INSET * 2,
                CELL - SEGMENT_INSET * 2,
            )
            pygame.draw.rect(surface, color, rect, border_radius=SEGMENT_RADIUS)

        # Eyes on the head, offset perpendicular to the travel direction.
        head_x, head_y = body[0]
        center_x = BOARD_X + head_x * CELL + CELL // 2
        center_y = BOARD_Y + head_y * CELL + CELL // 2
        dx, dy = self.state.direction
        px, py = -dy, dx
        for sign in (-1, 1):
            eye = (
                int(center_x + dx * 4 + px * 5 * sign),
                int(center_y + dy * 4 + py * 5 * sign),
            )
            pygame.draw.circle(surface, theme.BG, eye, 3)

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
