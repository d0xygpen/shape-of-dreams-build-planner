"""Memories tab - filterable memory catalog with detail panel."""

import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from gui.theme import PAD, PAD_SM, RARITY_COLORS
from gui.widgets.search_bar import SearchBar


class MemoriesTab(ttk.Frame):
    def __init__(self, parent, loader, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader
        self._all_rows = []
        self._memory_lookup = {}

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Top bar: search + keyword filter
        top = ttk.Frame(self)
        top.pack(fill="x", padx=PAD, pady=PAD)

        self._search = SearchBar(top, placeholder="Search memories...",
                                 on_change=self._on_filter)
        self._search.pack(side="left", fill="x", expand=True, padx=(0, PAD))

        ttk.Label(top, text="Keyword:").pack(side="left")
        self._keyword_var = ttk.StringVar(value="All")
        self._keyword_menu = ttk.Combobox(top, textvariable=self._keyword_var,
                                          width=16, state="readonly")
        self._keyword_menu.pack(side="left", padx=PAD_SM)
        self._keyword_menu.bind("<<ComboboxSelected>>", lambda _: self._on_filter())

        # Paned: table | detail
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        left = ttk.Frame(pane)
        pane.add(left, weight=2)

        cols = [
            {"text": "Name", "stretch": True, "width": 200},
            {"text": "Slots", "stretch": False, "width": 50},
            {"text": "Keywords", "stretch": True, "width": 180},
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
        # Count memory usage in builds
        usage = {}
        for builds in self.loader.builds.values():
            for build in builds:
                for m in build.get("memories", []):
                    name = m.get("name", "")
                    usage[name] = usage.get(name, 0) + 1

        # Collect all keywords
        all_keywords = set()

        self._all_rows = []
        self._memory_lookup = {}
        for mem in self.loader.memories:
            name = mem["name"]
            slots = mem.get("essence_slots", 0)
            keywords = mem.get("synergy_keywords", [])
            all_keywords.update(keywords)
            kw_str = ", ".join(keywords) if keywords else "-"
            count = usage.get(name, 0)
            self._all_rows.append((name, slots, kw_str, count))
            self._memory_lookup[name] = mem

        # Populate keyword filter
        sorted_kw = ["All"] + sorted(all_keywords)
        self._keyword_menu.configure(values=sorted_kw)

        self._on_filter()

    def _on_filter(self, _query: str = ""):
        query = self._search.query.lower()
        keyword_filter = self._keyword_var.get()

        filtered = []
        for row in self._all_rows:
            name, slots, kw_str, count = row

            # Keyword filter
            if keyword_filter != "All":
                mem = self._memory_lookup.get(name)
                if mem and keyword_filter not in mem.get("synergy_keywords", []):
                    continue

            # Search
            if query and query not in name.lower() and query not in kw_str.lower():
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
        mem = self._memory_lookup.get(name)
        if not mem:
            return

        # Clear and rebuild detail
        for w in self._detail.winfo_children():
            w.destroy()

        ttk.Label(self._detail, text=name, font=("Segoe UI", 14, "bold"),
                  bootstyle="light").pack(anchor="w", padx=PAD, pady=(PAD, 0))

        slots = mem.get("essence_slots", 0)
        ttk.Label(self._detail, text=f"Essence Slots: {slots}",
                  font=("Segoe UI", 11), bootstyle="secondary").pack(
            anchor="w", padx=PAD)

        ttk.Separator(self._detail).pack(fill="x", padx=PAD, pady=PAD)

        # Effect
        effect = mem.get("effect", mem.get("description", "N/A"))
        ttk.Label(self._detail, text="Effect", font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(anchor="w", padx=PAD)
        ttk.Label(self._detail, text=effect,
                  wraplength=350, font=("Segoe UI", 9)).pack(
            anchor="w", padx=PAD * 2, pady=4)

        # Synergy keywords
        keywords = mem.get("synergy_keywords", [])
        if keywords:
            ttk.Label(self._detail, text="Synergy Keywords",
                      font=("Segoe UI", 11, "bold"), bootstyle="info").pack(
                anchor="w", padx=PAD, pady=(PAD, 0))
            ttk.Label(self._detail, text=", ".join(keywords),
                      font=("Segoe UI", 9)).pack(anchor="w", padx=PAD * 2)

        # Compatible essences (ones matching keywords)
        if keywords:
            ttk.Separator(self._detail).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(self._detail, text="Compatible Essences",
                      font=("Segoe UI", 11, "bold"), bootstyle="success").pack(
                anchor="w", padx=PAD)

            kw_set = set(keywords)
            compatible = []
            for ess in self.loader.essences:
                ess_types = set(ess.get("synergy_types", []))
                overlap = kw_set.intersection(ess_types)
                if overlap:
                    compatible.append((ess, overlap))

            compatible.sort(key=lambda x: len(x[1]), reverse=True)
            for ess, overlap in compatible[:10]:
                rarity = ess.get("rarity", "Unknown")
                color = RARITY_COLORS.get(rarity, "#8B949E")
                ttk.Label(self._detail,
                          text=f"  [{rarity[0]}] {ess['name']} ({', '.join(overlap)})",
                          font=("Segoe UI", 9), foreground=color).pack(
                    anchor="w", padx=PAD)

        # Builds using this memory
        from analysis.build_comparator import BuildComparator
        comp = BuildComparator(self.loader)
        found = []
        for char, builds in self.loader.builds.items():
            for build in builds:
                for m in build.get("memories", []):
                    if m.get("name") == name:
                        found.append({"character": char, "build": build["name"]})
                        break

        if found:
            ttk.Separator(self._detail).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(self._detail, text=f"Used in {len(found)} build(s)",
                      font=("Segoe UI", 11, "bold"), bootstyle="success").pack(
                anchor="w", padx=PAD)
            for item in found[:8]:
                ttk.Label(self._detail,
                          text=f"  {item['character'].capitalize()} - {item['build']}",
                          font=("Segoe UI", 9)).pack(anchor="w", padx=PAD)
