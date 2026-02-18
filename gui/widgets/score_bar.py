"""Colored score bar widget (0-100)."""

import tkinter as tk
from gui.theme import score_color


class ScoreBar(tk.Canvas):
    """Horizontal progress bar with score-based coloring."""

    def __init__(self, parent, score: int = 0, width: int = 120, height: int = 16, **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, **kwargs)
        self._width = width
        self._height = height
        self.set_score(score)

    def set_score(self, score: int):
        self.delete("all")
        score = max(0, min(100, score))

        # Background
        self.create_rectangle(0, 0, self._width, self._height,
                              fill="#21262D", outline="#30363D")
        # Filled portion
        fill_w = int(self._width * score / 100)
        if fill_w > 0:
            color = score_color(score)
            self.create_rectangle(0, 0, fill_w, self._height,
                                  fill=color, outline="")
        # Score text
        self.create_text(self._width // 2, self._height // 2,
                         text=str(score), fill="#E6EDF3",
                         font=("Segoe UI", 8, "bold"))
