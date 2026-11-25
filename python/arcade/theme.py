"""Shared palette, fonts and drawing helpers for the canvas.

All games draw on a fixed 720x720 logical surface that the browser scales with
CSS. Keeping one palette in one file is what makes the two games look related.
"""

from __future__ import annotations

import pygame

# --- palette ----------------------------------------------------------------

BG = (9, 15, 27)
BOARD = (13, 23, 41)
BOARD_ALT = (16, 28, 48)
GRID = (31, 47, 75)
LINE = (44, 63, 92)
TEXT = (230, 237, 247)
MUTED = (147, 164, 189)
MINT = (52, 211, 153)
MINT_DARK = (20, 120, 92)
CORAL = (251, 113, 133)
CYAN = (56, 189, 248)
YELLOW = (250, 204, 21)
WHITE = (255, 255, 255)


class Fonts:
    """One font object per role. pygame's bundled default font needs no assets."""

    def __init__(self) -> None:
        self.huge = pygame.font.Font(None, 104)
        self.h1 = pygame.font.Font(None, 72)
        self.h2 = pygame.font.Font(None, 46)
        self.body = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, 24)
        self.tiny = pygame.font.Font(None, 20)


def text(
    surface: pygame.Surface,
    fonts: Fonts,
    message: object,
    style: str = "body",
    color: tuple[int, int, int] = TEXT,
    *,
    center: tuple[int, int] | None = None,
    topleft: tuple[int, int] | None = None,
    topright: tuple[int, int] | None = None,
    midtop: tuple[int, int] | None = None,
    midleft: tuple[int, int] | None = None,
    alpha: int = 255,
) -> pygame.Rect:
    """Render one line of text and return the rectangle it occupied.

    An anchor is required; passing ``center`` is the common case for status
    messages, ``topleft``/``topright`` for HUD corners.
    """
    image = getattr(fonts, style).render(str(message), True, color)
    if alpha < 255:
        image.set_alpha(alpha)

    if center is not None:
        rect = image.get_rect(center=center)
    elif topright is not None:
        rect = image.get_rect(topright=topright)
    elif midtop is not None:
        rect = image.get_rect(midtop=midtop)
    elif midleft is not None:
        rect = image.get_rect(midleft=midleft)
    elif topleft is not None:
        rect = image.get_rect(topleft=topleft)
    else:
        rect = image.get_rect(topleft=(0, 0))

    surface.blit(image, rect)
    return rect


def panel(
    surface: pygame.Surface,
    rect: pygame.Rect | tuple[int, int, int, int],
    *,
    color: tuple[int, int, int] = BOARD,
    border: tuple[int, int, int] = LINE,
    radius: int = 16,
    width: int = 1,
) -> None:
    """Filled rounded rectangle with a one-pixel border."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if width:
        pygame.draw.rect(surface, border, rect, width=width, border_radius=radius)


def overlay(surface: pygame.Surface, alpha: int = 180, color: tuple[int, int, int] = BG) -> None:
    """Dark translucent veil used by pause/game-over states."""
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((*color, alpha))
    surface.blit(veil, (0, 0))


def lerp_color(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    t: float,
) -> tuple[int, int, int]:
    """Linear blend between two RGB colors, clamped to t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    return tuple(round(a + (b - a) * t) for a, b in zip(start, end))  # type: ignore[return-value]
