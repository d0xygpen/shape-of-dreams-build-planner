"""
Main application window for Shape of Dreams Build Analyzer.

Provides sidebar navigation with character list, tabbed content area,
and a status bar. Wires up DataLoader and BuildAnalyzer for all tabs.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from analysis.data_loader import DataLoader
from analysis.build_analyzer import BuildAnalyzer

from gui.theme import (
    THEME, APP_TITLE, APP_VERSION,
    PAD, PAD_SM, PAD_LG, SIDEBAR_WIDTH,
)
from gui.tabs.builds_tab import BuildsTab
from gui.tabs.essences_tab import EssencesTab
from gui.tabs.memories_tab import MemoriesTab
from gui.tabs.compare_tab import CompareTab
from gui.tabs.synergy_tab import SynergyTab
from gui.tabs.meta_tab import MetaTab
from gui.tabs.create_tab import CreateTab


class BuildAnalyzerApp(ttk.Window):
    """Main application window."""

    def __init__(self):
        super().__init__(
            title=f"{APP_TITLE}  v{APP_VERSION}",
            themename=THEME,
            size=(1280, 800),
            minsize=(960, 600),
        )

        # Center on screen
        self.place_window_center()

        # Data layer
        self.loader = DataLoader()
        self.analyzer = BuildAnalyzer(self.loader)

        # Build UI
        self._setup_layout()
        self._setup_sidebar()
        self._setup_tabs()
        self._setup_statusbar()

    # ── Layout ────────────────────────────────────────────────────────

    def _setup_layout(self):
        """Create the main layout: sidebar | content."""
        self._main = ttk.Panedwindow(self, orient="horizontal")
        self._main.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ttk.Frame(self._main, width=SIDEBAR_WIDTH)
        self._main.add(self._sidebar, weight=0)

        # Content area
        self._content = ttk.Frame(self._main)
        self._main.add(self._content, weight=1)

    def _setup_sidebar(self):
        """Build the sidebar with title, character list, and stats."""
        # Title
        title_frame = ttk.Frame(self._sidebar)
        title_frame.pack(fill="x", padx=PAD, pady=(PAD_LG, PAD))

        ttk.Label(title_frame, text="Shape of",
                  font=("Segoe UI", 11), bootstyle="secondary").pack(anchor="w")
        ttk.Label(title_frame, text="Dreams",
                  font=("Segoe UI", 16, "bold"), bootstyle="light").pack(anchor="w")

        ttk.Separator(self._sidebar).pack(fill="x", padx=PAD, pady=PAD_SM)

        # Characters label
        ttk.Label(self._sidebar, text="CHARACTERS",
                  font=("Segoe UI", 9, "bold"),
                  bootstyle="secondary").pack(anchor="w", padx=PAD, pady=(PAD, PAD_SM))

        # "All" button
        self._char_buttons = {}
        all_btn = ttk.Button(self._sidebar, text="All Characters",
                             bootstyle="info-outline",
                             command=lambda: self._select_character(None))
        all_btn.pack(fill="x", padx=PAD, pady=1)
        self._char_buttons["all"] = all_btn

        # Container for character buttons (refreshable)
        self._char_btn_container = ttk.Frame(self._sidebar)
        self._char_btn_container.pack(fill="x")
        self._build_char_buttons()

        # Stats at bottom
        ttk.Separator(self._sidebar).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(self._sidebar, text="STATS",
                  font=("Segoe UI", 9, "bold"),
                  bootstyle="secondary").pack(anchor="w", padx=PAD, pady=(0, PAD_SM))

        self._stats_frame = ttk.Frame(self._sidebar)
        self._stats_frame.pack(fill="x")
        self._build_stats_labels()

        self._active_char = None

    def _build_char_buttons(self):
        """Build character buttons from all_builds (bundled + custom)."""
        for w in self._char_btn_container.winfo_children():
            w.destroy()
        # Remove old char keys (keep "all")
        self._char_buttons = {k: v for k, v in self._char_buttons.items()
                              if k == "all"}

        all_builds = self.loader.all_builds
        for char_name in sorted(all_builds.keys()):
            builds = all_builds[char_name]
            btn_text = f"{char_name.capitalize()}  ({len(builds)})"
            btn = ttk.Button(self._char_btn_container, text=btn_text,
                             bootstyle="secondary-outline",
                             command=lambda c=char_name: self._select_character(c))
            btn.pack(fill="x", padx=PAD, pady=1)
            self._char_buttons[char_name] = btn

    def _build_stats_labels(self):
        """Build the stats labels at the bottom of the sidebar."""
        for w in self._stats_frame.winfo_children():
            w.destroy()

        all_builds = self.loader.all_builds
        total_builds = sum(len(b) for b in all_builds.values())
        custom_count = sum(len(b) for b in self.loader.custom_builds.values())
        stats = [
            f"{len(all_builds)} characters",
            f"{total_builds} builds" + (f" ({custom_count} custom)"
                                        if custom_count else ""),
            f"{len(self.loader.essences)} essences",
            f"{len(self.loader.memories)} memories",
        ]
        for s in stats:
            ttk.Label(self._stats_frame, text=s,
                      font=("Segoe UI", 9), bootstyle="secondary").pack(
                anchor="w", padx=PAD * 2)

    def _refresh_sidebar(self):
        """Refresh character buttons and stats after custom build changes."""
        self._build_char_buttons()
        self._build_stats_labels()

    def _setup_tabs(self):
        """Create the tabbed content area."""
        self._notebook = ttk.Notebook(self._content)
        self._notebook.pack(fill="both", expand=True)

        # Create tabs
        self._builds_tab = BuildsTab(self._notebook, self.loader, self.analyzer)
        self._notebook.add(self._builds_tab, text="  Builds  ")

        self._create_tab = CreateTab(
            self._notebook, self.loader, self.analyzer,
            on_build_saved=self._on_custom_build_saved)
        self._notebook.add(self._create_tab, text="  Create  ")

        self._essences_tab = EssencesTab(self._notebook, self.loader)
        self._notebook.add(self._essences_tab, text="  Essences  ")

        self._memories_tab = MemoriesTab(self._notebook, self.loader)
        self._notebook.add(self._memories_tab, text="  Memories  ")

        self._compare_tab = CompareTab(self._notebook, self.loader, self.analyzer)
        self._notebook.add(self._compare_tab, text="  Compare  ")

        self._synergy_tab = SynergyTab(self._notebook, self.loader)
        self._notebook.add(self._synergy_tab, text="  Synergies  ")

        self._meta_tab = MetaTab(self._notebook, self.loader, self.analyzer)
        self._notebook.add(self._meta_tab, text="  Meta  ")

    def _on_custom_build_saved(self):
        """Refresh all tabs and sidebar after a custom build is saved/deleted."""
        self.loader.invalidate_cache()
        self._builds_tab._load_data()
        self._compare_tab._populate_dropdowns()
        self._create_tab._refresh_load_dropdown()
        self._refresh_sidebar()
        self._refresh_statusbar()

    def _setup_statusbar(self):
        """Create the bottom status bar."""
        self._statusbar = ttk.Frame(self)
        self._statusbar.pack(fill="x", side="bottom")

        ttk.Separator(self._statusbar).pack(fill="x")

        self._statusbar_inner = ttk.Frame(self._statusbar)
        self._statusbar_inner.pack(fill="x", padx=PAD, pady=PAD_SM)

        self._status_label = ttk.Label(
            self._statusbar_inner, text="",
            font=("Segoe UI", 9), bootstyle="secondary")
        self._status_label.pack(side="left")

        ttk.Label(self._statusbar_inner, text=f"v{APP_VERSION}",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(side="right")

        self._refresh_statusbar()

    def _refresh_statusbar(self):
        """Update the status bar text."""
        all_builds = self.loader.all_builds
        total_builds = sum(len(b) for b in all_builds.values())
        self._status_label.configure(
            text=f"{total_builds} builds  |  "
                 f"{len(self.loader.essences)} essences  |  "
                 f"{len(self.loader.memories)} memories  |  "
                 f"{len(all_builds)} characters")

    # ── Character filtering ───────────────────────────────────────────

    def _select_character(self, char_name=None):
        """Handle character selection in sidebar."""
        self._active_char = char_name

        # Update button styles
        for key, btn in self._char_buttons.items():
            if key == "all" and char_name is None:
                btn.configure(bootstyle="info")
            elif key == char_name:
                btn.configure(bootstyle="info")
            elif key == "all":
                btn.configure(bootstyle="info-outline")
            else:
                btn.configure(bootstyle="secondary-outline")

        # Filter builds tab
        self._builds_tab.filter_by_character(char_name)

        # Switch to builds tab
        self._notebook.select(0)


def run():
    """Launch the application."""
    app = BuildAnalyzerApp()
    app.mainloop()
