"""Meta tab - statistics dashboard with usage analytics."""

import tkinter as tk
import ttkbootstrap as ttk

from gui.theme import PAD, PAD_SM, PAD_LG, RARITY_COLORS, GRADE_COLORS, score_color
from gui.widgets.score_bar import ScoreBar


class MetaTab(ttk.Frame):
    def __init__(self, parent, loader, analyzer, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader
        self.analyzer = analyzer

        self._setup_ui()

    def _setup_ui(self):
        # Scrollable canvas
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        f = scroll_frame
        self._content = f

        # Title
        ttk.Label(f, text="Meta Report & Statistics",
                  font=("Segoe UI", 16, "bold"), bootstyle="light").pack(
            anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD))

        self._build_overview(f)
        self._character_comparison(f)
        self._essence_usage(f)
        self._unused_essences(f)
        self._common_pairs(f)

        # Bottom padding
        ttk.Label(f, text="").pack(pady=PAD_LG)

    def _build_overview(self, f):
        """Overall project statistics."""
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(f, text="Project Overview",
                  font=("Segoe UI", 14, "bold"), bootstyle="info").pack(
            anchor="w", padx=PAD_LG)

        meta = self.analyzer.essence_meta_report()

        stats_frame = ttk.Frame(f)
        stats_frame.pack(fill="x", padx=PAD_LG, pady=PAD)

        stats = [
            ("Characters", len(self.loader.character_names), "primary"),
            ("Total Builds", meta["total_builds"], "success"),
            ("Total Essences", meta["total_essences"], "info"),
            ("Used Essences", meta["used_essences"], "warning"),
            ("Total Memories", len(self.loader.memories), "info"),
        ]

        for i, (label, value, style) in enumerate(stats):
            card = ttk.Frame(stats_frame)
            card.pack(side="left", padx=PAD_SM, pady=PAD_SM, fill="x", expand=True)
            ttk.Label(card, text=label,
                      font=("Segoe UI", 9, "bold"),
                      bootstyle="secondary").pack(padx=PAD, pady=(PAD_SM, 0))
            ttk.Label(card, text=str(value),
                      font=("Segoe UI", 20, "bold"),
                      bootstyle=style).pack(padx=PAD, pady=(0, PAD))

    def _character_comparison(self, f):
        """Cross-character comparison table."""
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(f, text="Character Comparison",
                  font=("Segoe UI", 14, "bold"), bootstyle="info").pack(
            anchor="w", padx=PAD_LG)

        comparison = self.analyzer.cross_character_comparison()

        # Table header
        header = ttk.Frame(f)
        header.pack(fill="x", padx=PAD_LG, pady=(PAD, 0))
        cols = ["Character", "Builds", "Avg Score", "Best", "Worst", "Coverage"]
        widths = [120, 60, 80, 60, 60, 80]
        for col, w in zip(cols, widths):
            ttk.Label(header, text=col, font=("Segoe UI", 10, "bold"),
                      width=w // 8, bootstyle="secondary").pack(side="left", padx=2)

        ttk.Separator(f).pack(fill="x", padx=PAD_LG, pady=2)

        # Rows sorted by avg score
        sorted_chars = sorted(comparison.items(),
                              key=lambda x: x[1]["avg_score"], reverse=True)

        for char, info in sorted_chars:
            row = ttk.Frame(f)
            row.pack(fill="x", padx=PAD_LG, pady=1)

            ttk.Label(row, text=char.capitalize(),
                      font=("Segoe UI", 10, "bold"),
                      width=15).pack(side="left", padx=2)

            ttk.Label(row, text=str(info["build_count"]),
                      font=("Segoe UI", 10),
                      width=7).pack(side="left", padx=2)

            avg = info["avg_score"]
            avg_color = score_color(int(avg))
            ttk.Label(row, text=f"{avg:.1f}",
                      font=("Segoe UI", 10),
                      foreground=avg_color,
                      width=10).pack(side="left", padx=2)

            best_color = score_color(info["max_score"])
            ttk.Label(row, text=str(info["max_score"]),
                      font=("Segoe UI", 10),
                      foreground=best_color,
                      width=7).pack(side="left", padx=2)

            worst_color = score_color(info["min_score"])
            ttk.Label(row, text=str(info["min_score"]),
                      font=("Segoe UI", 10),
                      foreground=worst_color,
                      width=7).pack(side="left", padx=2)

            cov = info["archetype_coverage"]
            cov_color = score_color(int(cov))
            ttk.Label(row, text=f"{cov:.0f}%",
                      font=("Segoe UI", 10),
                      foreground=cov_color,
                      width=10).pack(side="left", padx=2)

    def _essence_usage(self, f):
        """Most used essences with horizontal bars."""
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(f, text="Most Used Essences",
                  font=("Segoe UI", 14, "bold"), bootstyle="info").pack(
            anchor="w", padx=PAD_LG)

        meta = self.analyzer.essence_meta_report()
        most_used = meta["most_used"][:15]

        if not most_used:
            ttk.Label(f, text="No usage data available",
                      bootstyle="secondary").pack(anchor="w", padx=PAD_LG)
            return

        max_count = most_used[0][1] if most_used else 1

        for name, count in most_used:
            row = ttk.Frame(f)
            row.pack(fill="x", padx=PAD_LG, pady=1)

            rarity = self.loader.essence_rarity_map.get(name, "Unknown")
            color = RARITY_COLORS.get(rarity, "#8B949E")

            ttk.Label(row, text=f"[{rarity[0]}] {name}",
                      font=("Segoe UI", 9), foreground=color,
                      width=30, anchor="w").pack(side="left")

            # Bar
            bar_width = 200
            bar = tk.Canvas(row, width=bar_width, height=14, highlightthickness=0)
            bar.pack(side="left", padx=PAD_SM)
            bar.create_rectangle(0, 0, bar_width, 14,
                                 fill="#21262D", outline="#30363D")
            fill_w = int(bar_width * count / max_count)
            if fill_w > 0:
                bar.create_rectangle(0, 0, fill_w, 14, fill=color, outline="")

            ttk.Label(row, text=f"x{count}",
                      font=("Segoe UI", 9, "bold"),
                      width=5).pack(side="left")

        # Rarity breakdown
        ttk.Label(f, text="Usage by Rarity",
                  font=("Segoe UI", 11, "bold"), bootstyle="warning").pack(
            anchor="w", padx=PAD_LG, pady=(PAD, 0))

        rarity_data = meta.get("usage_by_rarity", {})
        for rarity_name in ["Legendary", "Epic", "Unique", "Rare", "Common"]:
            data = rarity_data.get(rarity_name, {})
            if not data:
                continue
            color = RARITY_COLORS.get(rarity_name, "#8B949E")
            ttk.Label(f,
                      text=f"  {rarity_name}: {data.get('used', 0)} unique essences, "
                           f"{data.get('total_uses', 0)} total uses",
                      font=("Segoe UI", 9), foreground=color).pack(
                anchor="w", padx=PAD_LG)

    def _unused_essences(self, f):
        """List of essences not used in any build."""
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(f, text="Unused Essences",
                  font=("Segoe UI", 14, "bold"), bootstyle="danger").pack(
            anchor="w", padx=PAD_LG)

        meta = self.analyzer.essence_meta_report()
        unused = meta.get("unused_essences", [])

        if not unused:
            ttk.Label(f, text="All essences are used in at least one build!",
                      font=("Segoe UI", 10), bootstyle="success").pack(
                anchor="w", padx=PAD_LG, pady=PAD_SM)
            return

        ttk.Label(f, text=f"{len(unused)} essence(s) not used in any build:",
                  font=("Segoe UI", 10), bootstyle="secondary").pack(
            anchor="w", padx=PAD_LG, pady=PAD_SM)

        # Show in columns
        col_frame = ttk.Frame(f)
        col_frame.pack(fill="x", padx=PAD_LG)

        per_col = max(1, (len(unused) + 2) // 3)
        for col_idx in range(3):
            col = ttk.Frame(col_frame)
            col.pack(side="left", fill="y", expand=True, anchor="n")
            start = col_idx * per_col
            for name in unused[start:start + per_col]:
                rarity = self.loader.essence_rarity_map.get(name, "Unknown")
                color = RARITY_COLORS.get(rarity, "#8B949E")
                ttk.Label(col, text=f"[{rarity[0]}] {name}",
                          font=("Segoe UI", 9), foreground=color).pack(
                    anchor="w", padx=PAD_SM)

    def _common_pairs(self, f):
        """Most commonly co-occurring essence pairs."""
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        ttk.Label(f, text="Most Common Essence Pairs",
                  font=("Segoe UI", 14, "bold"), bootstyle="info").pack(
            anchor="w", padx=PAD_LG)
        ttk.Label(f, text="Essences that appear together most often across all builds:",
                  font=("Segoe UI", 10), bootstyle="secondary").pack(
            anchor="w", padx=PAD_LG, pady=(0, PAD_SM))

        meta = self.analyzer.essence_meta_report()
        pairs = meta.get("most_common_pairs", [])

        if not pairs:
            ttk.Label(f, text="No pair data available",
                      bootstyle="secondary").pack(anchor="w", padx=PAD_LG)
            return

        for p in pairs[:10]:
            pair_names = p["pair"]
            count = p["count"]

            row = ttk.Frame(f)
            row.pack(fill="x", padx=PAD_LG, pady=1)

            # Color each essence by rarity
            text_parts = []
            for name in pair_names:
                rarity = self.loader.essence_rarity_map.get(name, "Unknown")
                text_parts.append(f"[{rarity[0]}] {name}")

            pair_text = "  +  ".join(text_parts)
            ttk.Label(row, text=pair_text,
                      font=("Segoe UI", 10)).pack(side="left")
            ttk.Label(row, text=f"  (in {count} builds)",
                      font=("Segoe UI", 9), bootstyle="secondary").pack(side="left")
