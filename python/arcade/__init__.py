"""Arcade engine shared by every game.

Nothing in this package imports browser APIs: the same modules run under
WebAssembly (Pyodide) and under desktop Python for development and tests.
"""

from .actions import Action
from .app import App
from .scene import BaseScene

__all__ = ["Action", "App", "BaseScene"]
