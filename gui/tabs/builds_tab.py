"""Builds tab - master-detail view with Tableview and detail panel."""

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from gui.theme import PAD, GRADE_COLORS
from gui.widgets.search_bar import SearchBar
from gui.widgets.build_card import BuildDetailPanel


class BuildsTab(ttk.Frame):
    def __init__(self, parent, loader, analyzer, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader
        self.analyzer = analyzer
        self._all_rows = []
        self._char_filter = None
        self._build_lookup = {}

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Search bar at top
        top = ttk.Frame(self)
        top.pack(fill="x", padx=PAD, pady=PAD)
        self._search = SearchBar(top, placeholder="Search builds...",
                                 on_change=self._on_search)
        self._search.pack(fill="x")

        # Horizontal pane: table | detail
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        # Left: table
        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        cols = [
            {"text": "Character", "stretch": False, "width": 90},
            {"text": "Build Name", "stretch": True, "width": 220},
            {"text": "Score", "stretch": False, "width": 55},
            {"text": "Grade", "stretch": False, "width": 55},
            {"text": "Synergy", "stretch": False, "width": 65},
            {"text": "Complexity", "stretch": False, "width": 80},
            {"text": "Valid", "stretch": False, "width": 50},
            {"text": "Type", "stretch": False, "width": 60},
        ]
        self._table = Tableview(
            left,
            coldata=cols,
            rowdata=[],
            paginated=False,
            searchable=False,
            autofit=True,
            height=25,
        )
        self._table.pack(fill="both", expand=True)

        # Bind row selection
        self._table.view.bind("<<TreeviewSelect>>", self._on_select)

        # Right: detail panel
        self._detail = BuildDetailPanel(pane)
        pane.add(self._detail, weight=1)

    def _load_data(self):
        """Load all builds into the table."""
        self._all_rows = []
        self._build_lookup = {}

        for char_name, builds in sorted(self.loader.all_builds.items()):
            for build in builds:
                from analysis.validators import validate_no_duplicate_essences
                from analysis.synergies import score_essence_set

                # Score
                scorecard = self.analyzer.build_scorecard(char_name, build["name"])
                score = scorecard["score"]["total"] if scorecard else 0
                grade = scorecard["grade"] if scorecard else "?"

                # Synergy
                all_ess = set()
                for m in build.get("memories", []):
                    all_ess.update(m.get("essences", []))
                syn = score_essence_set(all_ess)

                # Complexity
                from analysis.build_comparator import BuildComparator
                comp = BuildComparator(self.loader)
                complexity = comp._calculate_complexity(build)

                # Valid
                dup = validate_no_duplicate_essences(build)
                valid = "Yes" if dup["valid"] else "No"

                # Type (Custom or blank)
                build_type = "Custom" if build.get("_custom") else ""

                row = (
                    char_name.capitalize(),
                    build["name"],
                    score,
                    grade,
                    syn,
                    complexity,
                    valid,
                    build_type,
                )
                self._all_rows.append(row)
                # Lookup key for detail
                key = f"{char_name}|{build['name']}"
                self._build_lookup[key] = (char_name, build)

        self._apply_filter()

    def _apply_filter(self):
        """Apply character and search filters to the table."""
        query = self._search.query.lower() if self._search else ""

        filtered = []
        for row in self._all_rows:
            char, name = row[0], row[1]

            # Character filter
            if self._char_filter and char.lower() != self._char_filter.lower():
                continue

            # Search filter
            if query and query not in name.lower() and query not in char.lower():
                continue

            filtered.append(row)

        self._table.delete_rows()
        self._table.insert_rows("end", filtered)
        self._table.load_table_data()

    def _on_search(self, _query: str):
        self._apply_filter()

    def filter_by_character(self, char_name: str = None):
        """Set character filter (None = show all)."""
        self._char_filter = char_name
        self._apply_filter()

    def _on_select(self, _event=None):
        """Handle row selection - show build detail."""
        selected = self._table.view.selection()
        if not selected:
            return
        item = self._table.view.item(selected[0])
        values = item.get("values", [])
        if len(values) < 2:
            return

        char = str(values[0]).lower()
        name = str(values[1])
        key = f"{char}|{name}"

        if key in self._build_lookup:
            char_name, build = self._build_lookup[key]
            self._detail.show_build(build, char_name, self.loader, self.analyzer)
