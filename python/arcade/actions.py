"""The vocabulary shared by input sources and game scenes.

Keyboard keys, on-screen touch buttons and (later) gamepads all get translated
into these values, so game logic never needs to know where an input came from.
"""

from enum import Enum


class Action(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    ACTION = "action"  # space/enter: confirm, or play again
    PAUSE = "pause"
    RESTART = "restart"
