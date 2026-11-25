"""Bounded input queue filled from JavaScript between frames.

The JS side calls ``boot.press("left")`` / ``boot.pointer_down(x, y)``. Those
calls land here; ``App.frame`` drains the queue once per rendered frame. Bounded
deques matter: a background tab can queue events for minutes and we must not
replay a thousand keystrokes when it wakes up.
"""

from collections import deque

from .actions import Action

MAX_ACTIONS = 32
MAX_POINTERS = 8


class InputQueue:
    def __init__(self) -> None:
        self._actions: deque[Action] = deque(maxlen=MAX_ACTIONS)
        self._pointers: deque[tuple[int, int]] = deque(maxlen=MAX_POINTERS)

    def push_action(self, action: Action | str) -> None:
        """Accept an Action or its string name (strings arrive from JS)."""
        if isinstance(action, str):
            try:
                action = Action(action.strip().lower())
            except ValueError:
                return
        self._actions.append(action)

    def push_pointer(self, x: int, y: int) -> None:
        self._pointers.append((int(x), int(y)))

    def drain_actions(self) -> list[Action]:
        actions = list(self._actions)
        self._actions.clear()
        return actions

    def drain_pointers(self) -> list[tuple[int, int]]:
        points = list(self._pointers)
        self._pointers.clear()
        return points

    def clear(self) -> None:
        self._actions.clear()
        self._pointers.clear()
