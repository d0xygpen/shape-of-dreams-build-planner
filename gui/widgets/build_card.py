"""Compact build summary card for the detail panel."""

import tkinter as tk
import ttkbootstrap as ttk
from gui.theme import (RARITY_COLORS, GRADE_COLORS, score_color,
                       PAD, PAD_SM, CUSTOM_BUILD_COLOR)
from gui.widgets.score_bar import ScoreBar


class BuildDetailPanel(ttk.Frame):
    """Right-side panel showing full build detail when a build is selected."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._widgets = []

    def clear(self):
        for w in self._widgets:
            w.destroy()
        self._widgets = []

    def show_build(self, build: dict, char_name: str, loader, analyzer):
        """Populate the panel with a build's full details."""
        self.clear()

        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel scrolling - scoped to when mouse is over this panel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))
        scroll_frame.bind("<Enter>",
                          lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        scroll_frame.bind("<Leave>",
                          lambda e: canvas.unbind_all("<MouseWheel>"))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._widgets.extend([canvas, scrollbar])

        f = scroll_frame

        # Header
        name = build.get("name", "Unknown")
        if build.get("_custom"):
            ttk.Label(f, text="CUSTOM BUILD",
                      font=("Segoe UI", 9, "bold"),
                      foreground=CUSTOM_BUILD_COLOR).pack(
                anchor="w", padx=PAD, pady=(PAD, 0))
        ttk.Label(f, text=name, font=("Segoe UI", 16, "bold"),
                  bootstyle="light").pack(anchor="w", padx=PAD,
                                          pady=(PAD if not build.get("_custom") else 0, 0))
        ttk.Label(f, text=f"Character: {char_name.capitalize()}",
                  font=("Segoe UI", 11), bootstyle="secondary").pack(
            anchor="w", padx=PAD)

        # Score
        scorecard = analyzer.build_scorecard(char_name, name)
        if scorecard:
            score_val = scorecard["score"]["total"]
            grade = scorecard["grade"]
            grade_color = GRADE_COLORS.get(grade, "#8B949E")

            sf = ttk.Frame(f)
            sf.pack(anchor="w", padx=PAD, pady=(PAD, 0))
            ttk.Label(sf, text=f"Grade: ", font=("Segoe UI", 12)).pack(side="left")
            ttk.Label(sf, text=grade, font=("Segoe UI", 14, "bold"),
                      foreground=grade_color).pack(side="left")
            ttk.Label(sf, text=f"  Score: {score_val}/100",
                      font=("Segoe UI", 12)).pack(side="left")

            bar = ScoreBar(f, score=score_val, width=200, height=18)
            bar.pack(anchor="w", padx=PAD, pady=PAD_SM)

            # Breakdown
            sc = scorecard["score"]
            for label, val, mx in [
                ("Synergy", sc["synergy"], 40),
                ("Rarity", sc["rarity"], 20),
                ("Validity", sc["validity"], 20),
                ("Completeness", sc["completeness"], 20),
            ]:
                row = ttk.Frame(f)
                row.pack(anchor="w", padx=PAD * 2, fill="x")
                ttk.Label(row, text=f"{label}:", width=14,
                          font=("Segoe UI", 9)).pack(side="left")
                mini = ScoreBar(row, score=int(val * 100 / mx), width=100, height=12)
                mini.pack(side="left", padx=PAD_SM)
                ttk.Label(row, text=f"{val}/{mx}",
                          font=("Segoe UI", 9)).pack(side="left")

        # Concept & Playstyle
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(f, text="Concept", font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(anchor="w", padx=PAD)
        ttk.Label(f, text=build.get("concept", "N/A"), wraplength=400,
                  font=("Segoe UI", 10)).pack(anchor="w", padx=PAD * 2, pady=PAD_SM)

        ttk.Label(f, text="Playstyle", font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(anchor="w", padx=PAD)
        ttk.Label(f, text=build.get("playstyle", "N/A"), wraplength=400,
                  font=("Segoe UI", 10)).pack(anchor="w", padx=PAD * 2, pady=PAD_SM)

        # Memories & Essences
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        memories = build.get("memories", [])
        ttk.Label(f, text=f"Memories ({len(memories)})",
                  font=("Segoe UI", 11, "bold"), bootstyle="info").pack(
            anchor="w", padx=PAD)

        for i, mem in enumerate(memories, 1):
            ttk.Label(f, text=f"  {i}. {mem.get('name', '?')}",
                      font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=PAD)
            for ess in mem.get("essences", []):
                rarity = loader.essence_rarity_map.get(ess, "Unknown")
                color = RARITY_COLORS.get(rarity, "#8B949E")
                ttk.Label(f, text=f"      [{rarity[0]}] {ess}",
                          font=("Segoe UI", 9), foreground=color).pack(
                    anchor="w", padx=PAD)
            if mem.get("rationale"):
                ttk.Label(f, text=f"      {mem['rationale']}",
                          font=("Segoe UI", 8), bootstyle="secondary",
                          wraplength=380).pack(anchor="w", padx=PAD * 2)

        # Synergies
        if scorecard and scorecard["score"]["synergy_details"]:
            ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(f, text="Active Synergies",
                      font=("Segoe UI", 11, "bold"), bootstyle="success").pack(
                anchor="w", padx=PAD)
            for s in scorecard["score"]["synergy_details"]:
                pair_str = " + ".join(s["pair"])
                ttk.Label(f, text=f"  [{s['score']}pts] {pair_str}",
                          font=("Segoe UI", 10, "bold"),
                          foreground="#E3B341").pack(anchor="w", padx=PAD)
                if s.get("description"):
                    ttk.Label(f, text=f"    {s['description']}",
                              font=("Segoe UI", 8), bootstyle="secondary",
                              wraplength=380).pack(anchor="w", padx=PAD * 2)

        # Strengths & Weaknesses
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        strengths = build.get("strengths", [])
        if strengths:
            ttk.Label(f, text="Strengths", font=("Segoe UI", 11, "bold"),
                      bootstyle="success").pack(anchor="w", padx=PAD)
            for s in strengths[:5]:
                ttk.Label(f, text=f"  + {s}", font=("Segoe UI", 9),
                          foreground="#3FB950").pack(anchor="w", padx=PAD)

        weaknesses = build.get("weaknesses", [])
        if weaknesses:
            ttk.Label(f, text="Weaknesses", font=("Segoe UI", 11, "bold"),
                      bootstyle="danger").pack(anchor="w", padx=PAD, pady=(PAD, 0))
            for w in weaknesses[:4]:
                ttk.Label(f, text=f"  - {w}", font=("Segoe UI", 9),
                          foreground="#F85149").pack(anchor="w", padx=PAD)

        # Strategy
        strategy = build.get("strategy", "")
        if strategy:
            ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(f, text="Strategy", font=("Segoe UI", 11, "bold"),
                      bootstyle="info").pack(anchor="w", padx=PAD)
            ttk.Label(f, text=strategy, wraplength=400,
                      font=("Segoe UI", 9)).pack(anchor="w", padx=PAD * 2, pady=PAD_SM)

        # Improvements
        if scorecard and scorecard.get("improvements"):
            ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
            ttk.Label(f, text="Suggested Improvements",
                      font=("Segoe UI", 11, "bold"), bootstyle="warning").pack(
                anchor="w", padx=PAD)
            for imp in scorecard["improvements"]:
                ttk.Label(f, text=f"  -> {imp}", font=("Segoe UI", 9),
                          foreground="#D29922").pack(anchor="w", padx=PAD)

        # Bottom padding
        ttk.Label(f, text="").pack(pady=PAD_SM)
