"""Essences tab - filterable essence catalog."""

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from gui.theme import PAD, PAD_SM, RARITY_COLORS
from gui.widgets.search_bar import SearchBar


class EssencesTab(ttk.Frame):
    def __init__(self, parent, loader, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader
        self._all_rows = []

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Top bar: search + rarity filter
        top = ttk.Frame(self)
        top.pack(fill="x", padx=PAD, pady=PAD)

        self._search = SearchBar(top, placeholder="Search essences...",
                                 on_change=self._on_filter)
        self._search.pack(side="left", fill="x", expand=True, padx=(0, PAD))

        ttk.Label(top, text="Rarity:").pack(side="left")
        self._rarity_var = ttk.StringVar(value="All")
        rarity_menu = ttk.Combobox(top, textvariable=self._rarity_var,
                                    values=["All", "Legendary", "Unique", "Epic", "Rare", "Common"],
                                    width=12, state="readonly")
        rarity_menu.pack(side="left", padx=PAD_SM)
        rarity_menu.bind("<<ComboboxSelected>>", lambda _: self._on_filter())

        # Paned: table | detail
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        left = ttk.Frame(pane)
        pane.add(left, weight=2)

        cols = [
            {"text": "Name", "stretch": True, "width": 200},
            {"text": "Rarity", "stretch": False, "width": 90},
            {"text": "Types", "stretch": True, "width": 150},
            {"text": "Used In", "stretch": False, "width": 65},
        ]
        self._table = Tableview(left, coldata=cols, rowdata=[],
                                 paginated=False, searchable=False,
                                 autofit=True, height=25)
        self._table.pack(fill="both", expand=True)
        self._table.view.bind("<<TreeviewSelect>>", self._on_select)

        # Right: detail
        self._detail = ttk.Frame(pane)
        pane.add(self._detail, weight=1)

    def _load_data(self):
        # Count usage
        usage = {}
        for builds in self.loader.builds.values():
            for build in builds:
                for m in build.get("memories", []):
                    for e in m.get("essences", []):
                        usage[e] = usage.get(e, 0) + 1

        self._all_rows = []
        self._essence_lookup = {}
        for ess in self.loader.essences:
            name = ess["name"]
            rarity = ess.get("rarity", "Unknown")
            types = ", ".join(ess.get("synergy_types", []))
            count = usage.get(name, 0)
            self._all_rows.append((name, rarity, types, count))
            self._essence_lookup[name] = ess

        self._on_filter()

    def _on_filter(self, _query: str = ""):
        query = self._search.query.lower()
        rarity = self._rarity_var.get()

        filtered = []
        for row in self._all_rows:
            name, r, types, count = row
            if rarity != "All" and r != rarity:
                continue
            if query and query not in name.lower() and query not in types.lower():
                continue
            filtered.append(row)

        self._table.delete_rows()
        self._table.insert_rows("end", filtered)
        self._table.load_table_data()

    def _on_select(self, _event=None):
        selected = self._table.view.selection()
        if not selected:
            return
        values = self._table.view.item(selected[0]).get("values", [])
        if not values:
            return

        name = str(values[0])
        ess = self._essence_lookup.get(name)
        if not ess:
            return

        # Clear and rebuild detail
        for w in self._detail.winfo_children():
            w.destroy()

        rarity = ess.get("rarity", "Unknown")
        color = RARITY_COLORS.get(rarity, "#8B949E")

        ttk.Label(self._detail, text=name, font=("Segoe UI", 14, "bold"),
                  foreground=color).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        ttk.Label(self._detail, text=rarity, font=("Segoe UI", 11),
                  foreground=color).pack(anchor="w", padx=PAD)

        ttk.Separator(self._detail).pack(fill="x", padx=PAD, pady=PAD)

        ttk.Label(self._detail, text="Effect", font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(anchor="w", padx=PAD)
        ttk.Label(self._detail, text=ess.get("effect", "N/A"),
                  wraplength=350, font=("Segoe UI", 9)).pack(
            anchor="w", padx=PAD * 2, pady=4)

        types = ess.get("synergy_types", [])
        if types:
            ttk.Label(self._detail, text="Synergy Types",
                      font=("Segoe UI", 11, "bold"), bootstyle="info").pack(
                anchor="w", padx=PAD, pady=(PAD, 0))
            ttk.Label(self._detail, text=", ".join(types),
                      font=("Segoe UI", 9)).pack(anchor="w", padx=PAD * 2)

        # Builds using this essence
        from analysis.build_comparator import BuildComparator
        comp = BuildComparator(self.loader)
        found = comp.find_builds_with_essence(name)
        if found:
            ttk.Separator(self._detail).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(self._detail, text=f"Used in {len(found)} build(s)",
                      font=("Segoe UI", 11, "bold"), bootstyle="success").pack(
                anchor="w", padx=PAD)
            for item in found[:8]:
                ttk.Label(self._detail,
                          text=f"  {item['character'].capitalize()} - {item['build']}",
                          font=("Segoe UI", 9)).pack(anchor="w", padx=PAD)

        # Substitutes
        from analysis.synergy_analyzer import SynergyAnalyzer
        sa = SynergyAnalyzer(self.loader)
        subs = sa.suggest_substitutes(name)
        if subs:
            ttk.Separator(self._detail).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(self._detail, text="Substitutes",
                      font=("Segoe UI", 11, "bold"), bootstyle="warning").pack(
                anchor="w", padx=PAD)
            for sub in subs[:5]:
                sub_color = RARITY_COLORS.get(sub["rarity"], "#8B949E")
                ttk.Label(self._detail,
                          text=f"  {sub['essence']} ({sub['rarity']}) - {', '.join(sub['shared_types'])}",
                          font=("Segoe UI", 9), foreground=sub_color).pack(
                    anchor="w", padx=PAD)
