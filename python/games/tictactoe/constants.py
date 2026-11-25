"""Tic-Tac-Toe: board geometry and tuning constants."""

CELL = 160
BOARD = CELL * 3            # 480
BOARD_X = (720 - BOARD) // 2  # 120
BOARD_Y = 150

AI_DELAY = 0.45             # pause before the AI answers, so it feels deliberate
MARK_INSET = 38             # distance from a cell's edge to an X/O stroke
MARK_WIDTH = 10
GRID_WIDTH = 4
