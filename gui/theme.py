"""
Theme constants and style configuration for the GUI.
ARPG-standard rarity colors, score gradients, and layout constants.
"""

# Rarity colors (ARPG convention)
RARITY_COLORS = {
    "Common": "#8B949E",
    "Rare": "#58A6FF",
    "Epic": "#BC8CFF",
    "Legendary": "#E3B341",
    "Unique": "#3FB950",
    "Unknown": "#484F58",
}

# Score-to-color gradient
def score_color(score: int) -> str:
    if score >= 81:
        return "#3FB950"  # green
    elif score >= 61:
        return "#58A6FF"  # blue
    elif score >= 41:
        return "#D29922"  # amber
    elif score >= 21:
        return "#F0883E"  # orange
    return "#F85149"  # red

# Grade-to-color
GRADE_COLORS = {
    "S": "#E3B341",
    "A": "#3FB950",
    "B": "#58A6FF",
    "C": "#D29922",
    "D": "#F0883E",
    "F": "#F85149",
}

# Semantic colors
SUCCESS = "#3FB950"
WARNING = "#D29922"
ERROR = "#F85149"
INFO = "#58A6FF"
CUSTOM_BUILD_COLOR = "#58A6FF"

# Layout
SIDEBAR_WIDTH = 200
PAD = 8
PAD_SM = 4
PAD_LG = 16

# Theme name (ttkbootstrap built-in)
THEME = "darkly"

# App metadata
APP_TITLE = "Shape of Dreams - Build Planner"
APP_VERSION = "1.1.0"
