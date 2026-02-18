"""Compare tab - side-by-side build comparison with diff highlighting."""

import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import PAD, PAD_SM, RARITY_COLORS, GRADE_COLORS, score_color
from gui.widgets.score_bar import ScoreBar


class CompareTab(ttk.Frame):
    def __init__(self, parent, loader, analyzer, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader
        self.analyzer = analyzer

        self._build_map = {}   # display_name -> (char, build_dict)
        self._setup_ui()
        self._populate_dropdowns()

    def _setup_ui(self):
        # Top: two dropdowns
        top = ttk.Frame(self)
        top.pack(fill="x", padx=PAD, pady=PAD)

        ttk.Label(top, text="Build A:", font=("Segoe UI", 11, "bold")).pack(side="left")
        self._var_a = ttk.StringVar()
        self._combo_a = ttk.Combobox(top, textvariable=self._var_a,
                                     width=35, state="readonly")
        self._combo_a.pack(side="left", padx=(PAD_SM, PAD))

        ttk.Label(top, text="vs", font=("Segoe UI", 12, "bold"),
                  bootstyle="warning").pack(side="left", padx=PAD)

        ttk.Label(top, text="Build B:", font=("Segoe UI", 11, "bold")).pack(side="left")
        self._var_b = ttk.StringVar()
        self._combo_b = ttk.Combobox(top, textvariable=self._var_b,
                                     width=35, state="readonly")
        self._combo_b.pack(side="left", padx=(PAD_SM, PAD))

        ttk.Button(top, text="Compare", bootstyle="primary",
                   command=self._compare).pack(side="left", padx=PAD)

        # Content: scrollable comparison
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical",
                                        command=self._canvas.yview)
        self._scroll_frame = ttk.Frame(self._canvas)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        def _on_mousewheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._canvas.bind("<Enter>",
                          lambda e: self._canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self._canvas.bind("<Leave>",
                          lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        # Placeholder text
        ttk.Label(self._scroll_frame,
                  text="Select two builds and click Compare",
                  font=("Segoe UI", 14), bootstyle="secondary").pack(
            anchor="center", pady=40)

    def _populate_dropdowns(self):
        self._build_map = {}
        names = []
        for char, builds in sorted(self.loader.all_builds.items()):
            for build in builds:
                prefix = "[Custom] " if build.get("_custom") else ""
                display = f"{prefix}{char.capitalize()} - {build['name']}"
                self._build_map[display] = (char, build)
                names.append(display)

        self._combo_a.configure(values=names)
        self._combo_b.configure(values=names)

    def _compare(self):
        a_name = self._var_a.get()
        b_name = self._var_b.get()
        if not a_name or not b_name:
            return
        if a_name == b_name:
            return

        a_info = self._build_map.get(a_name)
        b_info = self._build_map.get(b_name)
        if not a_info or not b_info:
            return

        char_a, build_a = a_info
        char_b, build_b = b_info

        # Clear existing content
        for w in self._scroll_frame.winfo_children():
            w.destroy()

        # Scorecards
        sc_a = self.analyzer.build_scorecard(char_a, build_a["name"])
        sc_b = self.analyzer.build_scorecard(char_b, build_b["name"])

        # Side-by-side container
        container = ttk.Frame(self._scroll_frame)
        container.pack(fill="x", padx=PAD, pady=PAD)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.columnconfigure(2, weight=1)

        # Headers
        ttk.Label(container, text=build_a["name"],
                  font=("Segoe UI", 14, "bold"), bootstyle="info").grid(
            row=0, column=0, sticky="w", padx=PAD)
        ttk.Label(container, text="vs",
                  font=("Segoe UI", 14, "bold"), bootstyle="warning").grid(
            row=0, column=1, padx=PAD)
        ttk.Label(container, text=build_b["name"],
                  font=("Segoe UI", 14, "bold"), bootstyle="info").grid(
            row=0, column=2, sticky="w", padx=PAD)

        ttk.Label(container, text=f"({char_a.capitalize()})",
                  font=("Segoe UI", 10), bootstyle="secondary").grid(
            row=1, column=0, sticky="w", padx=PAD)
        ttk.Label(container, text=f"({char_b.capitalize()})",
                  font=("Segoe UI", 10), bootstyle="secondary").grid(
            row=1, column=2, sticky="w", padx=PAD)

        row = 2

        # Score comparison
        row = self._add_separator(container, row)
        row = self._add_section_header(container, row, "Overall Score")

        if sc_a and sc_b:
            score_a = sc_a["score"]["total"]
            score_b = sc_b["score"]["total"]
            grade_a = sc_a["grade"]
            grade_b = sc_b["grade"]

            row = self._add_score_row(container, row, "Score",
                                      f"{score_a}/100", f"{score_b}/100",
                                      score_a, score_b)
            row = self._add_score_row(container, row, "Grade",
                                      grade_a, grade_b,
                                      score_a, score_b)

            # Breakdown
            for label, key, mx in [
                ("Synergy", "synergy", 40),
                ("Rarity", "rarity", 20),
                ("Validity", "validity", 20),
                ("Completeness", "completeness", 20),
            ]:
                va = sc_a["score"][key]
                vb = sc_b["score"][key]
                row = self._add_score_row(container, row, label,
                                          f"{va}/{mx}", f"{vb}/{mx}", va, vb)

        # Essence comparison
        row = self._add_separator(container, row)
        row = self._add_section_header(container, row, "Essences")

        ess_a = set()
        for m in build_a.get("memories", []):
            ess_a.update(m.get("essences", []))
        ess_b = set()
        for m in build_b.get("memories", []):
            ess_b.update(m.get("essences", []))

        shared = ess_a & ess_b
        only_a = ess_a - ess_b
        only_b = ess_b - ess_a

        if shared:
            row = self._add_label_row(container, row, "Shared Essences:",
                                      bootstyle="secondary")
            for ess in sorted(shared):
                rarity = self.loader.essence_rarity_map.get(ess, "Unknown")
                color = RARITY_COLORS.get(rarity, "#8B949E")
                lbl = ttk.Label(container,
                                text=f"  [{rarity[0]}] {ess}",
                                font=("Segoe UI", 9), foreground=color)
                lbl.grid(row=row, column=0, columnspan=3, sticky="w", padx=PAD * 2)
                row += 1

        if only_a:
            row = self._add_essence_list(container, row, "Only in A:", only_a, col=0)
        if only_b:
            row = self._add_essence_list(container, row, "Only in B:", only_b, col=2)

        # Memory comparison
        row = self._add_separator(container, row)
        row = self._add_section_header(container, row, "Memories")

        mem_a = [m.get("name", "?") for m in build_a.get("memories", [])]
        mem_b = [m.get("name", "?") for m in build_b.get("memories", [])]

        mem_shared = set(mem_a) & set(mem_b)
        mem_only_a = set(mem_a) - set(mem_b)
        mem_only_b = set(mem_b) - set(mem_a)

        a_frame = ttk.Frame(container)
        a_frame.grid(row=row, column=0, sticky="nw", padx=PAD)
        for mn in mem_a:
            style = "success" if mn in mem_shared else "light"
            ttk.Label(a_frame, text=f"  {mn}", font=("Segoe UI", 9),
                      bootstyle=style).pack(anchor="w")

        b_frame = ttk.Frame(container)
        b_frame.grid(row=row, column=2, sticky="nw", padx=PAD)
        for mn in mem_b:
            style = "success" if mn in mem_shared else "light"
            ttk.Label(b_frame, text=f"  {mn}", font=("Segoe UI", 9),
                      bootstyle=style).pack(anchor="w")
        row += 1

        # Strengths comparison
        row = self._add_separator(container, row)
        row = self._add_section_header(container, row, "Strengths")

        str_a_frame = ttk.Frame(container)
        str_a_frame.grid(row=row, column=0, sticky="nw", padx=PAD)
        for s in build_a.get("strengths", [])[:5]:
            ttk.Label(str_a_frame, text=f"  + {s}", font=("Segoe UI", 9),
                      foreground="#3FB950").pack(anchor="w")

        str_b_frame = ttk.Frame(container)
        str_b_frame.grid(row=row, column=2, sticky="nw", padx=PAD)
        for s in build_b.get("strengths", [])[:5]:
            ttk.Label(str_b_frame, text=f"  + {s}", font=("Segoe UI", 9),
                      foreground="#3FB950").pack(anchor="w")
        row += 1

        # Weaknesses comparison
        row = self._add_section_header(container, row, "Weaknesses")

        wk_a_frame = ttk.Frame(container)
        wk_a_frame.grid(row=row, column=0, sticky="nw", padx=PAD)
        for w in build_a.get("weaknesses", [])[:4]:
            ttk.Label(wk_a_frame, text=f"  - {w}", font=("Segoe UI", 9),
                      foreground="#F85149").pack(anchor="w")

        wk_b_frame = ttk.Frame(container)
        wk_b_frame.grid(row=row, column=2, sticky="nw", padx=PAD)
        for w in build_b.get("weaknesses", [])[:4]:
            ttk.Label(wk_b_frame, text=f"  - {w}", font=("Segoe UI", 9),
                      foreground="#F85149").pack(anchor="w")
        row += 1

        # Bottom padding
        ttk.Label(container, text="").grid(row=row, column=0, pady=PAD)

    # ── Helper methods ────────────────────────────────────────────────

    def _add_separator(self, container, row):
        sep = ttk.Separator(container)
        sep.grid(row=row, column=0, columnspan=3, sticky="ew", padx=PAD, pady=PAD)
        return row + 1

    def _add_section_header(self, container, row, text):
        ttk.Label(container, text=text, font=("Segoe UI", 12, "bold"),
                  bootstyle="info").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=PAD, pady=(0, PAD_SM))
        return row + 1

    def _add_score_row(self, container, row, label, val_a, val_b,
                       num_a, num_b):
        ttk.Label(container, text=f"{label}: {val_a}",
                  font=("Segoe UI", 10),
                  foreground="#3FB950" if num_a > num_b else (
                      "#F85149" if num_a < num_b else "#8B949E")
                  ).grid(row=row, column=0, sticky="w", padx=PAD * 2)
        diff = num_a - num_b
        diff_text = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "="
        diff_color = "#3FB950" if diff > 0 else ("#F85149" if diff < 0 else "#8B949E")
        ttk.Label(container, text=diff_text, font=("Segoe UI", 10, "bold"),
                  foreground=diff_color).grid(row=row, column=1)
        ttk.Label(container, text=f"{label}: {val_b}",
                  font=("Segoe UI", 10),
                  foreground="#3FB950" if num_b > num_a else (
                      "#F85149" if num_b < num_a else "#8B949E")
                  ).grid(row=row, column=2, sticky="w", padx=PAD * 2)
        return row + 1

    def _add_label_row(self, container, row, text, bootstyle="light"):
        ttk.Label(container, text=text, font=("Segoe UI", 10, "bold"),
                  bootstyle=bootstyle).grid(
            row=row, column=0, columnspan=3, sticky="w", padx=PAD)
        return row + 1

    def _add_essence_list(self, container, row, title, essences, col=0):
        ttk.Label(container, text=title, font=("Segoe UI", 10, "bold"),
                  bootstyle="warning").grid(row=row, column=col, sticky="w", padx=PAD)
        row += 1
        for ess in sorted(essences):
            rarity = self.loader.essence_rarity_map.get(ess, "Unknown")
            color = RARITY_COLORS.get(rarity, "#8B949E")
            ttk.Label(container, text=f"  [{rarity[0]}] {ess}",
                      font=("Segoe UI", 9), foreground=color).grid(
                row=row, column=col, sticky="w", padx=PAD * 2)
            row += 1
        return row
