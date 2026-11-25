"""Snake: board geometry and tuning constants.

All values are in logical 720x720 canvas pixels. ``BOARD_X``/``BOARD_Y`` center
the 22x22 grid, leaving room for the HUD above and a hint below.
"""

COLS = 22
ROWS = 22
CELL = 28

BOARD_WIDTH = COLS * CELL   # 616
BOARD_HEIGHT = ROWS * CELL  # 616
BOARD_X = (720 - BOARD_WIDTH) // 2
BOARD_Y = 76

BASE_INTERVAL = 0.135   # seconds per grid move at score 0
MIN_INTERVAL = 0.065    # fastest the snake is allowed to move
SPEED_PER_POINT = 0.0005  # seconds shaved off per food eaten

FOOD_SCORE = 10

# Look
SEGMENT_INSET = 3
SEGMENT_RADIUS = 7
FOOD_RADIUS = 8
