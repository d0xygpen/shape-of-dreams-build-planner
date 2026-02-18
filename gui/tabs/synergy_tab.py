"""Synergy tab - synergy pair browser, calculator, and substitute finder."""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.tableview import Tableview

from gui.theme import PAD, PAD_SM, RARITY_COLORS
from gui.widgets.search_bar import SearchBar

from analysis.synergies import (
    ESSENCE_SYNERGIES,
    SYNERGY_CATEGORIES,
    SOLO_ESSENCE_SCORES,
    score_essence_set,
    find_all_synergies_in_set,
)


class SynergyTab(ttk.Frame):
    def __init__(self, parent, loader, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader

        self._setup_ui()

    def _setup_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # Tab 1: Known synergy pairs
        self._pairs_frame = ttk.Frame(notebook)
        notebook.add(self._pairs_frame, text="Synergy Pairs")
        self._setup_pairs_tab()

        # Tab 2: Synergy calculator
        self._calc_frame = ttk.Frame(notebook)
        notebook.add(self._calc_frame, text="Calculator")
        self._setup_calc_tab()

        # Tab 3: Categories
        self._cat_frame = ttk.Frame(notebook)
        notebook.add(self._cat_frame, text="Categories")
        self._setup_categories_tab()

    def _setup_pairs_tab(self):
        """Show all known synergy pairs in a table."""
        cols = [
            {"text": "Essence A", "stretch": True, "width": 180},
            {"text": "Essence B", "stretch": True, "width": 180},
            {"text": "Score", "stretch": False, "width": 60},
            {"text": "Description", "stretch": True, "width": 350},
        ]

        rows = []
        for (e1, e2), info in ESSENCE_SYNERGIES.items():
            rows.append((e1, e2, info["score"], info["description"]))

        # Add solo essences
        for name, score in SOLO_ESSENCE_SCORES.items():
            rows.append((name, "(standalone)", score, f"{name} provides standalone value"))

        # Sort by score descending
        rows.sort(key=lambda r: r[2], reverse=True)

        table = Tableview(self._pairs_frame, coldata=cols, rowdata=rows,
                          paginated=False, searchable=False,
                          autofit=True, height=20)
        table.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # Summary
        total_pairs = len(ESSENCE_SYNERGIES) + len(SOLO_ESSENCE_SCORES)
        ttk.Label(self._pairs_frame,
                  text=f"{total_pairs} known synergies  |  "
                       f"Max pair score: {max(i['score'] for i in ESSENCE_SYNERGIES.values())}  |  "
                       f"Avg pair score: {sum(i['score'] for i in ESSENCE_SYNERGIES.values()) // len(ESSENCE_SYNERGIES)}",
                  font=("Segoe UI", 9), bootstyle="secondary").pack(
            anchor="w", padx=PAD, pady=(0, PAD))

    def _setup_calc_tab(self):
        """Let user pick essences and see synergy score."""
        top = ttk.Frame(self._calc_frame)
        top.pack(fill="x", padx=PAD, pady=PAD)

        ttk.Label(top, text="Select essences to calculate synergy score:",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")

        # Essence selector area
        selector = ttk.Frame(self._calc_frame)
        selector.pack(fill="x", padx=PAD, pady=PAD_SM)

        # Available essences listbox
        left = ttk.LabelFrame(selector, text="Available Essences")
        left.pack(side="left", fill="both", expand=True, padx=(0, PAD_SM))

        self._search_calc = SearchBar(left, placeholder="Filter essences...",
                                      on_change=self._filter_available)
        self._search_calc.pack(fill="x", padx=PAD_SM, pady=PAD_SM)

        self._available_list = ttk.Treeview(left, columns=("name", "rarity"),
                                            show="headings", height=12)
        self._available_list.heading("name", text="Name")
        self._available_list.heading("rarity", text="Rarity")
        self._available_list.column("name", width=200)
        self._available_list.column("rarity", width=80)
        self._available_list.pack(fill="both", expand=True, padx=PAD_SM, pady=(0, PAD_SM))

        # Buttons
        mid = ttk.Frame(selector)
        mid.pack(side="left", padx=PAD_SM)
        ttk.Button(mid, text="Add >>", bootstyle="success-outline",
                   command=self._add_essence).pack(pady=PAD_SM)
        ttk.Button(mid, text="<< Remove", bootstyle="danger-outline",
                   command=self._remove_essence).pack(pady=PAD_SM)
        ttk.Button(mid, text="Clear All", bootstyle="secondary-outline",
                   command=self._clear_selected).pack(pady=PAD_SM)

        # Selected essences listbox
        right = ttk.LabelFrame(selector, text="Selected Essences")
        right.pack(side="left", fill="both", expand=True, padx=(PAD_SM, 0))

        self._selected_list = ttk.Treeview(right, columns=("name", "rarity"),
                                           show="headings", height=12)
        self._selected_list.heading("name", text="Name")
        self._selected_list.heading("rarity", text="Rarity")
        self._selected_list.column("name", width=200)
        self._selected_list.column("rarity", width=80)
        self._selected_list.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)

        # Results area
        self._result_frame = ttk.LabelFrame(self._calc_frame, text="Synergy Results")
        self._result_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        self._result_label = ttk.Label(self._result_frame,
                                       text="Add essences to see synergy analysis",
                                       font=("Segoe UI", 10),
                                       bootstyle="secondary")
        self._result_label.pack(anchor="w", padx=PAD, pady=PAD)

        # Load available essences
        self._selected_essences = set()
        self._load_available()

    def _load_available(self):
        if not hasattr(self, "_available_list"):
            return
        for item in self._available_list.get_children():
            self._available_list.delete(item)

        query = self._search_calc.query.lower() if hasattr(self, "_search_calc") else ""
        for ess in self.loader.essences:
            name = ess["name"]
            if name in self._selected_essences:
                continue
            if query and query not in name.lower():
                continue
            rarity = ess.get("rarity", "Unknown")
            self._available_list.insert("", "end", values=(name, rarity))

    def _filter_available(self, _query=""):
        self._load_available()

    def _add_essence(self):
        selected = self._available_list.selection()
        if not selected:
            return
        for item in selected:
            values = self._available_list.item(item, "values")
            name = values[0]
            self._selected_essences.add(name)

        self._load_available()
        self._refresh_selected()
        self._calculate()

    def _remove_essence(self):
        selected = self._selected_list.selection()
        if not selected:
            return
        for item in selected:
            values = self._selected_list.item(item, "values")
            name = values[0]
            self._selected_essences.discard(name)

        self._load_available()
        self._refresh_selected()
        self._calculate()

    def _clear_selected(self):
        self._selected_essences.clear()
        self._load_available()
        self._refresh_selected()
        self._calculate()

    def _refresh_selected(self):
        for item in self._selected_list.get_children():
            self._selected_list.delete(item)
        for name in sorted(self._selected_essences):
            rarity = self.loader.essence_rarity_map.get(name, "Unknown")
            self._selected_list.insert("", "end", values=(name, rarity))

    def _calculate(self):
        # Clear results
        for w in self._result_frame.winfo_children():
            w.destroy()

        if not self._selected_essences:
            ttk.Label(self._result_frame,
                      text="Add essences to see synergy analysis",
                      font=("Segoe UI", 10), bootstyle="secondary").pack(
                anchor="w", padx=PAD, pady=PAD)
            return

        score = score_essence_set(self._selected_essences)
        synergies = find_all_synergies_in_set(self._selected_essences)

        # Score display
        score_color_val = "#3FB950" if score >= 40 else (
            "#58A6FF" if score >= 20 else (
                "#D29922" if score >= 10 else "#F85149"))

        ttk.Label(self._result_frame,
                  text=f"Total Synergy Score: {score}",
                  font=("Segoe UI", 14, "bold"),
                  foreground=score_color_val).pack(anchor="w", padx=PAD, pady=(PAD, PAD_SM))

        ttk.Label(self._result_frame,
                  text=f"{len(self._selected_essences)} essences selected, "
                       f"{len(synergies)} synergies found",
                  font=("Segoe UI", 10), bootstyle="secondary").pack(
            anchor="w", padx=PAD)

        if synergies:
            ttk.Separator(self._result_frame).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(self._result_frame, text="Active Synergies:",
                      font=("Segoe UI", 11, "bold"), bootstyle="success").pack(
                anchor="w", padx=PAD)

            for s in synergies:
                pair_str = " + ".join(s["pair"])
                ttk.Label(self._result_frame,
                          text=f"  [{s['score']}pts] {pair_str}",
                          font=("Segoe UI", 10, "bold"),
                          foreground="#E3B341").pack(anchor="w", padx=PAD)
                if s.get("description"):
                    ttk.Label(self._result_frame,
                              text=f"    {s['description']}",
                              font=("Segoe UI", 8), bootstyle="secondary",
                              wraplength=500).pack(anchor="w", padx=PAD * 2)

    def _setup_categories_tab(self):
        """Show synergy categories and which essences belong to each."""
        canvas = tk.Canvas(self._cat_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self._cat_frame, orient="vertical",
                                  command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        f = scroll_frame

        ttk.Label(f, text="Synergy Categories",
                  font=("Segoe UI", 14, "bold"), bootstyle="light").pack(
            anchor="w", padx=PAD, pady=PAD)
        ttk.Label(f, text="Essences are grouped by their synergy types. "
                          "Essences in the same category tend to work well together.",
                  font=("Segoe UI", 10), bootstyle="secondary",
                  wraplength=600).pack(anchor="w", padx=PAD, pady=(0, PAD))

        for cat_name, types in sorted(SYNERGY_CATEGORIES.items()):
            ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD_SM)

            cat_label = cat_name.replace("_", " ").title()
            ttk.Label(f, text=cat_label,
                      font=("Segoe UI", 12, "bold"), bootstyle="info").pack(
                anchor="w", padx=PAD)
            ttk.Label(f, text=f"Types: {', '.join(types)}",
                      font=("Segoe UI", 9), bootstyle="secondary").pack(
                anchor="w", padx=PAD * 2)

            # Find essences matching this category
            type_set = set(types)
            matching = []
            for ess in self.loader.essences:
                ess_types = set(ess.get("synergy_types", []))
                overlap = type_set & ess_types
                if overlap:
                    matching.append(ess)

            if matching:
                for ess in matching[:12]:
                    rarity = ess.get("rarity", "Unknown")
                    color = RARITY_COLORS.get(rarity, "#8B949E")
                    ess_types = ", ".join(ess.get("synergy_types", []))
                    ttk.Label(f,
                              text=f"  [{rarity[0]}] {ess['name']} - {ess_types}",
                              font=("Segoe UI", 9), foreground=color).pack(
                        anchor="w", padx=PAD * 2)
            else:
                ttk.Label(f, text="  (no matching essences)",
                          font=("Segoe UI", 9), bootstyle="secondary").pack(
                    anchor="w", padx=PAD * 2)

        ttk.Label(f, text="").pack(pady=PAD)
