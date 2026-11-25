"""Fixed-timestep accumulator.

Rendering runs as fast as the display allows (60/120/144 Hz); simulation runs in
fixed slices. ``FixedStep.advance`` converts one variable frame delta into the
number of whole game ticks that are due.

Why it matters: a game tick of 0.13 s must feel identical on every monitor, and
after a tab switch (where dt can be several seconds) it must not replay hundreds
of ticks at once.
"""


class FixedStep:
    def __init__(self, max_frame: float = 0.25, max_steps: int = 8) -> None:
        self.max_frame = max_frame
        self.max_steps = max_steps
        self._accumulator = 0.0

    def advance(self, dt: float, interval: float) -> int:
        """Return how many fixed ``interval`` ticks fit in ``dt`` seconds."""
        if interval <= 0:
            return 0
        self._accumulator += min(max(dt, 0.0), self.max_frame)
        steps = 0
        while self._accumulator >= interval and steps < self.max_steps:
            self._accumulator -= interval
            steps += 1
        return steps

    @property
    def remainder(self) -> float:
        """Leftover time, useful for interpolating the next tick's position."""
        return self._accumulator

    def reset(self) -> None:
        self._accumulator = 0.0
