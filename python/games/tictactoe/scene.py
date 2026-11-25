"""Tic-Tac-Toe's pygame scene: clicks, the AI turn timer and rendering.

The human is always X and moves first. A finished round waits for a tap (with a
short grace period) or the R key before resetting, so nobody loses a game by
clicking the square that ended it.
"""

from __future__ import annotations

import math
import random

import pygame

from arcade import theme
from arcade.actions import Action
from arcade.scene import BaseScene

from .ai import best_move
from .constants import (
    AI_DELAY,
    BOARD,
    BOARD_X,
    BOARD_Y,
    CELL,
    GRID_WIDTH,
    MARK_INSET,
    MARK_WIDTH,
)
from .logic import (
    DRAW,
    EMPTY,
    O,
    X,
    Board,
    apply_move,
    new_board,
    winning_line,
    winner,
)

WIN_KEY = "ttt.wins"
LOSS_KEY = "ttt.losses"
DRAW_KEY = "ttt.draws"


def build_scene(screen: pygame.Surface, fonts: theme.Fonts, scores) -> "TicTacToeScene":
    return TicTacToeScene(screen, fonts, scores)


class TicTacToeScene(BaseScene):
    slug = "tictactoe"
    title = "Tic-Tac-Toe"

    def __init__(self, screen: pygame.Surface, fonts: theme.Fonts, scores) -> None:
        super().__init__(screen, fonts, scores)
        self.rng = random.Random()
        self.reset()

    # --- setup -------------------------------------------------------------

    def reset(self) -> None:
        super().reset()
        self.board: Board = new_board()
        self.turn = X
        self.ai_timer = 0.0
        self.result: int | None = None
        self.win_line: tuple[int, int, int] | None = None
        self.recorded = False

        self.wins = int(self.scores.get(WIN_KEY, 0))
        self.losses = int(self.scores.get(LOSS_KEY, 0))
        self.draws = int(self.scores.get(DRAW_KEY, 0))

    # --- input -------------------------------------------------------------

    def on_pointer(self, x: int, y: int) -> None:
        if self.result is not None or self.turn != X:
            return
        index = self._cell_at(x, y)
        if index is None or self.board[index] != EMPTY:
            return

        self._play(index, X)
        if self.result is None:
            self.turn = O
            self.ai_timer = AI_DELAY

    def _cell_at(self, x: int, y: int) -> int | None:
        if not (BOARD_X <= x < BOARD_X + BOARD and BOARD_Y <= y < BOARD_Y + BOARD):
            return None
        column = int((x - BOARD_X) // CELL)
        row = int((y - BOARD_Y) // CELL)
        return row * 3 + column

    def _play(self, index: int, player: int) -> None:
        self.board = apply_move(self.board, index, player)
        line = winning_line(self.board)
        outcome = winner(self.board)
        if outcome is None:
            return

        self.result = outcome
        self.win_line = line
        self.finish()
        self._record(outcome)

    def _record(self, outcome: int) -> None:
        if self.recorded:
            return
        self.recorded = True
        if outcome == X:
            self.wins += 1
            self.scores.set(WIN_KEY, self.wins)
        elif outcome == O:
            self.losses += 1
            self.scores.set(LOSS_KEY, self.losses)
        elif outcome == DRAW:
            self.draws += 1
            self.scores.set(DRAW_KEY, self.draws)

    # --- simulation --------------------------------------------------------

    def tick(self, dt: float) -> None:
        if self.result is not None or self.turn != O:
            return

        self.ai_timer -= dt
        if self.ai_timer > 0:
            return

        index = best_move(self.board, O)
        if index is None:
            return
        self._play(index, O)
        if self.result is None:
            self.turn = X

    # --- rendering ---------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BG)

        theme.text(surface, self.fonts, "TIC-TAC-TOE", "small", theme.MUTED, topleft=(BOARD_X, 36))
        theme.text(
            surface, self.fonts, "YOU ARE X", "small", theme.CORAL,
            topright=(self.width - BOARD_X, 36),
        )

        self._draw_status(surface)

        panel = (BOARD_X - 20, BOARD_Y - 20, BOARD + 40, BOARD + 40)
        theme.panel(surface, panel, radius=18)

        for step in (1, 2):
            offset = BOARD_X + step * CELL
            pygame.draw.line(
                surface, theme.GRID,
                (offset, BOARD_Y + 12), (offset, BOARD_Y + BOARD - 12), GRID_WIDTH,
            )
            offset_y = BOARD_Y + step * CELL
            pygame.draw.line(
                surface, theme.GRID,
                (BOARD_X + 12, offset_y), (BOARD_X + BOARD - 12, offset_y), GRID_WIDTH,
            )

        self._draw_win_line(surface)

        for index, cell in enumerate(self.board):
            if cell == X:
                self._draw_x(surface, index)
            elif cell == O:
                self._draw_o(surface, index)

        theme.text(
            surface,
            self.fonts,
            f"YOU {self.wins}    ·    DRAWS {self.draws}    ·    AI {self.losses}",
            "small",
            theme.MUTED,
            center=(self.width // 2, 684),
        )

        if self.result is not None:
            alpha = 120 + int(105 * (0.5 + 0.5 * math.sin(self.time * 4.0)))
            theme.text(
                surface, self.fonts, "Tap to play again", "tiny", theme.MUTED,
                center=(self.width // 2, 710), alpha=alpha,
            )

    def _draw_status(self, surface: pygame.Surface) -> None:
        if self.result is None:
            if self.turn == X:
                label, color = "Your turn", theme.TEXT
            else:
                dots = "." * (1 + int(self.time * 3) % 3)
                label, color = f"AI is thinking{dots}", theme.CYAN
        elif self.result == X:
            label, color = "You win!", theme.MINT
        elif self.result == O:
            label, color = "The AI wins", theme.CORAL
        else:
            label, color = "A draw", theme.MUTED

        theme.text(surface, self.fonts, label, "h2", color, center=(self.width // 2, 100))

    def _draw_win_line(self, surface: pygame.Surface) -> None:
        if self.win_line is None:
            return
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for index in self.win_line:
            cx, cy = self._center(index)
            rect = pygame.Rect(0, 0, CELL - 16, CELL - 16)
            rect.center = (cx, cy)
            pygame.draw.rect(layer, (52, 211, 153, 30), rect, border_radius=12)
            pygame.draw.rect(layer, (52, 211, 153, 130), rect, width=2, border_radius=12)
        surface.blit(layer, (0, 0))

    def _center(self, index: int) -> tuple[int, int]:
        column, row = index % 3, index // 3
        return (
            BOARD_X + column * CELL + CELL // 2,
            BOARD_Y + row * CELL + CELL // 2,
        )

    def _draw_x(self, surface: pygame.Surface, index: int) -> None:
        cx, cy = self._center(index)
        reach = CELL // 2 - MARK_INSET
        pygame.draw.line(
            surface, theme.CORAL, (cx - reach, cy - reach), (cx + reach, cy + reach), MARK_WIDTH,
        )
        pygame.draw.line(
            surface, theme.CORAL, (cx + reach, cy - reach), (cx - reach, cy + reach), MARK_WIDTH,
        )

    def _draw_o(self, surface: pygame.Surface, index: int) -> None:
        cx, cy = self._center(index)
        pygame.draw.circle(surface, theme.CYAN, (cx, cy), CELL // 2 - MARK_INSET, MARK_WIDTH)
