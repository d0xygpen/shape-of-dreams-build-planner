"""Reusable memory slot widget for the Build Creator tab."""

import ttkbootstrap as ttk
from gui.theme import PAD, PAD_SM, RARITY_COLORS


class MemorySlotWidget(ttk.Frame):
    """A single memory slot: memory dropdown, 3 essence dropdowns, rationale."""

    def __init__(self, parent, slot_number, memory_names, essence_names,
                 rarity_map, on_change=None, on_remove=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.slot_number = slot_number
        self._memory_names = memory_names
        self._essence_names = essence_names
        self._rarity_map = rarity_map
        self._on_change = on_change
        self._on_remove = on_remove

        self._setup_ui()

    def _setup_ui(self):
        # Header row: "Memory N" + Remove button
        header = ttk.Frame(self)
        header.pack(fill="x", padx=PAD_SM, pady=(PAD_SM, 0))

        ttk.Label(header, text=f"Memory {self.slot_number}",
                  font=("Segoe UI", 10, "bold"),
                  bootstyle="info").pack(side="left")

        if self._on_remove:
            ttk.Button(header, text="X", width=3,
                       bootstyle="danger-outline",
                       command=self._on_remove).pack(side="right")

        # Memory dropdown
        mem_row = ttk.Frame(self)
        mem_row.pack(fill="x", padx=PAD_SM * 2, pady=(PAD_SM, 0))
        ttk.Label(mem_row, text="Memory:", width=9,
                  font=("Segoe UI", 9)).pack(side="left")
        self._mem_var = ttk.StringVar()
        self._mem_combo = ttk.Combobox(mem_row, textvariable=self._mem_var,
                                       values=self._memory_names,
                                       state="readonly", width=30)
        self._mem_combo.pack(side="left", padx=PAD_SM)
        self._mem_combo.bind("<<ComboboxSelected>>", self._notify_change)

        # Essence dropdowns (3 slots)
        self._ess_vars = []
        self._ess_combos = []
        self._ess_labels = []

        for i in range(3):
            row = ttk.Frame(self)
            row.pack(fill="x", padx=PAD_SM * 2, pady=1)
            ttk.Label(row, text=f"Essence {i+1}:", width=9,
                      font=("Segoe UI", 9)).pack(side="left")
            var = ttk.StringVar()
            combo = ttk.Combobox(row, textvariable=var,
                                 values=self._essence_names,
                                 state="readonly", width=30)
            combo.pack(side="left", padx=PAD_SM)
            combo.bind("<<ComboboxSelected>>",
                       lambda e, idx=i: self._on_essence_selected(idx))

            # Rarity indicator label
            rlabel = ttk.Label(row, text="", font=("Segoe UI", 8))
            rlabel.pack(side="left", padx=PAD_SM)

            self._ess_vars.append(var)
            self._ess_combos.append(combo)
            self._ess_labels.append(rlabel)

        # Rationale entry
        rat_row = ttk.Frame(self)
        rat_row.pack(fill="x", padx=PAD_SM * 2, pady=(PAD_SM, PAD_SM))
        ttk.Label(rat_row, text="Rationale:", width=9,
                  font=("Segoe UI", 9)).pack(side="left")
        self._rationale_var = ttk.StringVar()
        self._rationale_entry = ttk.Entry(rat_row,
                                          textvariable=self._rationale_var,
                                          width=40)
        self._rationale_entry.pack(side="left", padx=PAD_SM, fill="x", expand=True)

        # Separator
        ttk.Separator(self).pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))

    def _on_essence_selected(self, idx):
        """Update rarity label when an essence is selected."""
        name = self._ess_vars[idx].get()
        rarity = self._rarity_map.get(name, "Unknown")
        color = RARITY_COLORS.get(rarity, RARITY_COLORS["Unknown"])
        self._ess_labels[idx].configure(text=f"[{rarity}]", foreground=color)
        self._notify_change()

    def _notify_change(self, _event=None):
        if self._on_change:
            self._on_change()

    # ── Public API ───────────────────────────────────────────────────

    @property
    def memory_name(self) -> str:
        return self._mem_var.get()

    @property
    def essences(self) -> list:
        return [v.get() for v in self._ess_vars if v.get()]

    @property
    def rationale(self) -> str:
        return self._rationale_var.get().strip()

    def set_values(self, memory_name: str, essences: list,
                   rationale: str = ""):
        """Populate from an existing build's memory entry."""
        self._mem_var.set(memory_name)
        for i, ess in enumerate(essences[:3]):
            self._ess_vars[i].set(ess)
            self._on_essence_selected(i)
        self._rationale_var.set(rationale)

    def clear(self):
        """Reset all fields."""
        self._mem_var.set("")
        for i in range(3):
            self._ess_vars[i].set("")
            self._ess_labels[i].configure(text="")
        self._rationale_var.set("")

    def to_dict(self) -> dict:
        """Convert to build-schema memory entry dict."""
        d = {
            "name": self.memory_name,
            "essences": self.essences,
        }
        if self.rationale:
            d["rationale"] = self.rationale
        return d
