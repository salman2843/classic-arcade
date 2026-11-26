"""2048: board geometry and tuning constants."""

SIZE = 4
TARGET = 2048
SPAWN_FOUR_CHANCE = 0.1  # 90% of new tiles are 2, 10% are 4

# Canvas geometry. The grid is 4 cells plus 3 gaps, centred on 720x720.
CELL = 132
GAP = 12
BOARD_X = (720 - (SIZE * CELL + (SIZE - 1) * GAP)) // 2  # 78
BOARD_Y = 118
TILE_RADIUS = 10
BOARD_PADDING = 12
