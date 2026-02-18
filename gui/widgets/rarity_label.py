"""Color-coded rarity badge label."""

import ttkbootstrap as ttk
from gui.theme import RARITY_COLORS


class RarityLabel(ttk.Label):
    """Label that auto-colors based on rarity tier."""

    def __init__(self, parent, text: str, rarity: str = "Unknown", **kwargs):
        color = RARITY_COLORS.get(rarity, RARITY_COLORS["Unknown"])
        super().__init__(parent, text=text, foreground=color, **kwargs)
        self._rarity = rarity

    def set_rarity(self, text: str, rarity: str):
        color = RARITY_COLORS.get(rarity, RARITY_COLORS["Unknown"])
        self.configure(text=text, foreground=color)
