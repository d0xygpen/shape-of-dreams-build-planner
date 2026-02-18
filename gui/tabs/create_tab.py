"""Build Creator tab - create, edit, and save custom builds."""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk

from analysis.synergies import score_essence_set, find_all_synergies_in_set
from analysis.validators import validate_no_duplicate_essences
from gui.theme import (
    PAD, PAD_SM, PAD_LG,
    SUCCESS, WARNING, ERROR, CUSTOM_BUILD_COLOR,
    RARITY_COLORS,
)
from gui.widgets.memory_slot import MemorySlotWidget
from gui.widgets.score_bar import ScoreBar


class CreateTab(ttk.Frame):
    """Tab for creating and editing custom builds."""

    MAX_MEMORIES = 4

    def __init__(self, parent, loader, analyzer,
                 on_build_saved=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.loader = loader
        self.analyzer = analyzer
        self._on_build_saved = on_build_saved
        self._memory_slots = []
        self._debounce_id = None
        self._editing_custom = False  # True when editing existing custom build

        # Precompute dropdown values
        self._memory_names = sorted(m["name"] for m in self.loader.memories)
        self._essence_names = sorted(e["name"] for e in self.loader.essences)
        self._char_names = sorted(
            set(c["name"] for c in self.loader.characters) | {"General"}
        )

        self._setup_ui()

    # ── UI Setup ─────────────────────────────────────────────────────

    def _setup_ui(self):
        # Scrollable canvas
        self._canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=self._canvas.yview)
        self._scroll_frame = ttk.Frame(self._canvas)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.create_window((0, 0), window=self._scroll_frame,
                                   anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)

        # Mousewheel scrolling (scoped to hover)
        def _on_mousewheel(event):
            self._canvas.yview_scroll(
                int(-1 * (event.delta / 120)), "units")
        self._canvas.bind(
            "<Enter>",
            lambda e: self._canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self._canvas.bind(
            "<Leave>",
            lambda e: self._canvas.unbind_all("<MouseWheel>"))
        self._scroll_frame.bind(
            "<Enter>",
            lambda e: self._canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self._scroll_frame.bind(
            "<Leave>",
            lambda e: self._canvas.unbind_all("<MouseWheel>"))

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        f = self._scroll_frame

        # ── Title ────────────────────────────────────────────────────
        ttk.Label(f, text="Build Creator",
                  font=("Segoe UI", 16, "bold"),
                  bootstyle="light").pack(anchor="w", padx=PAD, pady=(PAD, 0))
        ttk.Label(f, text="Create and save your own custom builds",
                  font=("Segoe UI", 10),
                  bootstyle="secondary").pack(anchor="w", padx=PAD)

        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)

        # ── Character + Build Name row ───────────────────────────────
        top_row = ttk.Frame(f)
        top_row.pack(fill="x", padx=PAD, pady=PAD_SM)

        ttk.Label(top_row, text="Character:",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self._char_var = ttk.StringVar()
        self._char_combo = ttk.Combobox(
            top_row, textvariable=self._char_var,
            values=self._char_names, state="readonly", width=15)
        self._char_combo.pack(side="left", padx=(PAD_SM, PAD_LG))
        self._char_combo.bind("<<ComboboxSelected>>",
                              lambda e: self._schedule_update())

        ttk.Label(top_row, text="Build Name:",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self._name_var = ttk.StringVar()
        self._name_entry = ttk.Entry(top_row, textvariable=self._name_var,
                                     width=35)
        self._name_entry.pack(side="left", padx=PAD_SM)
        self._name_var.trace_add("write", lambda *_: self._schedule_update())

        # ── Concept + Playstyle ──────────────────────────────────────
        for label_text, attr_name in [("Concept", "_concept_text"),
                                      ("Playstyle", "_playstyle_text")]:
            ttk.Label(f, text=label_text,
                      font=("Segoe UI", 10, "bold"),
                      bootstyle="info").pack(anchor="w", padx=PAD,
                                              pady=(PAD_SM, 0))
            text = tk.Text(f, height=2, width=70, wrap="word",
                           font=("Segoe UI", 9),
                           bg="#2b3035", fg="#e8e8e8",
                           insertbackground="#e8e8e8",
                           relief="flat", padx=6, pady=4)
            text.pack(fill="x", padx=PAD * 2, pady=PAD_SM)
            setattr(self, attr_name, text)

        # ── Memory Slots ─────────────────────────────────────────────
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        mem_header = ttk.Frame(f)
        mem_header.pack(fill="x", padx=PAD)
        ttk.Label(mem_header, text="Memories (4 slots, 3 essences each)",
                  font=("Segoe UI", 11, "bold"),
                  bootstyle="info").pack(side="left")

        self._slots_container = ttk.Frame(f)
        self._slots_container.pack(fill="x", padx=PAD)

        # Start with 1 empty slot
        self._add_memory_slot()

        # Add Memory button
        self._add_mem_btn = ttk.Button(
            f, text="+ Add Memory", bootstyle="success-outline",
            command=self._add_memory_slot)
        self._add_mem_btn.pack(anchor="w", padx=PAD * 2, pady=PAD_SM)

        # ── Synergy Preview + Validation (side by side) ──────────────
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        preview_row = ttk.Frame(f)
        preview_row.pack(fill="x", padx=PAD)

        # Left: Synergy Preview
        syn_frame = ttk.Frame(preview_row)
        syn_frame.pack(side="left", fill="both", expand=True, padx=(0, PAD))
        ttk.Label(syn_frame, text="Synergy Preview",
                  font=("Segoe UI", 11, "bold"),
                  bootstyle="success").pack(anchor="w")
        self._syn_score_label = ttk.Label(
            syn_frame, text="Score: --",
            font=("Segoe UI", 10))
        self._syn_score_label.pack(anchor="w", padx=PAD_SM)
        self._syn_bar = ScoreBar(syn_frame, score=0, width=200, height=16)
        self._syn_bar.pack(anchor="w", padx=PAD_SM, pady=PAD_SM)
        self._syn_details_frame = ttk.Frame(syn_frame)
        self._syn_details_frame.pack(anchor="w", fill="x")

        # Right: Validation
        val_frame = ttk.Frame(preview_row)
        val_frame.pack(side="right", fill="both", expand=True, padx=(PAD, 0))
        ttk.Label(val_frame, text="Validation",
                  font=("Segoe UI", 11, "bold"),
                  bootstyle="warning").pack(anchor="w")
        self._val_frame = ttk.Frame(val_frame)
        self._val_frame.pack(anchor="w", fill="x")

        # ── Strategy + Strengths + Weaknesses ────────────────────────
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)

        ttk.Label(f, text="Strategy",
                  font=("Segoe UI", 10, "bold"),
                  bootstyle="info").pack(anchor="w", padx=PAD)
        self._strategy_text = tk.Text(
            f, height=2, width=70, wrap="word",
            font=("Segoe UI", 9),
            bg="#2b3035", fg="#e8e8e8",
            insertbackground="#e8e8e8",
            relief="flat", padx=6, pady=4)
        self._strategy_text.pack(fill="x", padx=PAD * 2, pady=PAD_SM)

        str_weak_row = ttk.Frame(f)
        str_weak_row.pack(fill="x", padx=PAD, pady=PAD_SM)

        # Strengths
        left = ttk.Frame(str_weak_row)
        left.pack(side="left", fill="both", expand=True, padx=(0, PAD))
        ttk.Label(left, text="Strengths (one per line)",
                  font=("Segoe UI", 10, "bold"),
                  foreground=SUCCESS).pack(anchor="w")
        self._strengths_text = tk.Text(
            left, height=4, width=35, wrap="word",
            font=("Segoe UI", 9),
            bg="#2b3035", fg="#e8e8e8",
            insertbackground="#e8e8e8",
            relief="flat", padx=6, pady=4)
        self._strengths_text.pack(fill="x")

        # Weaknesses
        right = ttk.Frame(str_weak_row)
        right.pack(side="right", fill="both", expand=True, padx=(PAD, 0))
        ttk.Label(right, text="Weaknesses (one per line)",
                  font=("Segoe UI", 10, "bold"),
                  foreground=ERROR).pack(anchor="w")
        self._weaknesses_text = tk.Text(
            right, height=4, width=35, wrap="word",
            font=("Segoe UI", 9),
            bg="#2b3035", fg="#e8e8e8",
            insertbackground="#e8e8e8",
            relief="flat", padx=6, pady=4)
        self._weaknesses_text.pack(fill="x")

        # ── Action Buttons ───────────────────────────────────────────
        ttk.Separator(f).pack(fill="x", padx=PAD, pady=PAD)
        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", padx=PAD, pady=(0, PAD))

        self._save_btn = ttk.Button(
            btn_row, text="Save Build", bootstyle="success",
            command=self._save_build)
        self._save_btn.pack(side="left", padx=(0, PAD))

        ttk.Button(btn_row, text="Clear / Reset",
                   bootstyle="secondary-outline",
                   command=self._clear_form).pack(side="left", padx=(0, PAD))

        ttk.Label(btn_row, text="Load existing:",
                  font=("Segoe UI", 9)).pack(side="left", padx=(PAD_LG, PAD_SM))
        self._load_var = ttk.StringVar()
        self._load_combo = ttk.Combobox(
            btn_row, textvariable=self._load_var,
            state="readonly", width=35)
        self._load_combo.pack(side="left", padx=PAD_SM)
        self._load_combo.bind("<<ComboboxSelected>>", self._on_load_selected)
        self._refresh_load_dropdown()

        self._delete_btn = ttk.Button(
            btn_row, text="Delete", bootstyle="danger-outline",
            command=self._delete_build, state="disabled")
        self._delete_btn.pack(side="right")

        # Bottom padding
        ttk.Label(f, text="").pack(pady=PAD)

    # ── Memory Slot Management ───────────────────────────────────────

    def _add_memory_slot(self):
        if len(self._memory_slots) >= self.MAX_MEMORIES:
            return
        slot_num = len(self._memory_slots) + 1
        slot = MemorySlotWidget(
            self._slots_container,
            slot_number=slot_num,
            memory_names=self._memory_names,
            essence_names=self._essence_names,
            rarity_map=self.loader.essence_rarity_map,
            on_change=self._schedule_update,
            on_remove=lambda s=slot_num: self._remove_memory_slot(s),
        )
        slot.pack(fill="x", pady=PAD_SM)
        self._memory_slots.append(slot)
        self._update_add_btn()
        self._schedule_update()

    def _remove_memory_slot(self, slot_num):
        if len(self._memory_slots) <= 1:
            return
        # Remove the slot widget
        idx = slot_num - 1
        if idx < len(self._memory_slots):
            self._memory_slots[idx].destroy()
            self._memory_slots.pop(idx)
            # Renumber remaining slots
            for i, slot in enumerate(self._memory_slots):
                slot.slot_number = i + 1
            self._update_add_btn()
            self._schedule_update()

    def _update_add_btn(self):
        if len(self._memory_slots) >= self.MAX_MEMORIES:
            self._add_mem_btn.configure(state="disabled")
        else:
            self._add_mem_btn.configure(state="normal")

    # ── Debounced Update ─────────────────────────────────────────────

    def _schedule_update(self):
        """Debounce: update preview after 300ms of no changes."""
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self._update_preview)

    def _update_preview(self):
        """Recalculate synergy score and validation."""
        self._debounce_id = None
        self._update_synergy_preview()
        self._update_validation()

    # ── Synergy Preview ──────────────────────────────────────────────

    def _update_synergy_preview(self):
        all_essences = set()
        for slot in self._memory_slots:
            all_essences.update(slot.essences)

        # Clear old details
        for w in self._syn_details_frame.winfo_children():
            w.destroy()

        if not all_essences:
            self._syn_score_label.configure(text="Score: --")
            self._syn_bar.update_score(0)
            return

        syn_score = score_essence_set(all_essences)
        synergies = find_all_synergies_in_set(all_essences)

        self._syn_score_label.configure(
            text=f"Score: {syn_score}  |  {len(synergies)} synergies found")
        # Approximate 0-100 scale (40 is max synergy component)
        bar_score = min(100, int(syn_score * 100 / 80))
        self._syn_bar.update_score(bar_score)

        for s in synergies:
            pair_str = " + ".join(s["pair"])
            ttk.Label(
                self._syn_details_frame,
                text=f"  [{s['score']}pts] {pair_str}",
                font=("Segoe UI", 9, "bold"),
                foreground="#E3B341",
            ).pack(anchor="w")

    # ── Validation ───────────────────────────────────────────────────

    def _update_validation(self):
        for w in self._val_frame.winfo_children():
            w.destroy()

        errors = []
        warnings = []
        ok_items = []

        # Build name
        name = self._name_var.get().strip()
        if not name:
            errors.append("Build name is required")
        else:
            ok_items.append("Build name set")

        # Character
        if not self._char_var.get():
            errors.append("Character is required")
        else:
            ok_items.append("Character selected")

        # At least 1 memory with essences
        has_memory = False
        for slot in self._memory_slots:
            if slot.memory_name and slot.essences:
                has_memory = True
                break
        if not has_memory:
            errors.append("At least 1 memory with essences required")
        else:
            ok_items.append("Memories configured")

        # Build a preview dict for duplicate checking
        preview = self._build_dict()
        if preview:
            dup_result = validate_no_duplicate_essences(preview)
            if not dup_result["valid"]:
                for d in dup_result["duplicates"]:
                    errors.append(f"Duplicate essence: {d}")
            else:
                ok_items.append("No duplicate essences")

            # Check essence references
            all_ess = set()
            for m in preview.get("memories", []):
                all_ess.update(m.get("essences", []))
            for ess_name in all_ess:
                if ess_name not in self.loader.essence_by_name:
                    warnings.append(f"Unknown essence: {ess_name}")

            # Check memory references
            for m in preview.get("memories", []):
                mname = m.get("name", "")
                if mname and mname not in self.loader.memory_by_name:
                    warnings.append(f"Unknown memory: {mname}")

        # Render
        for e in errors:
            ttk.Label(self._val_frame,
                      text=f"  [X] {e}",
                      font=("Segoe UI", 9),
                      foreground=ERROR).pack(anchor="w")
        for w in warnings:
            ttk.Label(self._val_frame,
                      text=f"  [!] {w}",
                      font=("Segoe UI", 9),
                      foreground=WARNING).pack(anchor="w")
        for o in ok_items:
            ttk.Label(self._val_frame,
                      text=f"  [ok] {o}",
                      font=("Segoe UI", 9),
                      foreground=SUCCESS).pack(anchor="w")

        # Enable/disable save button
        self._save_btn.configure(
            state="normal" if not errors else "disabled")

    # ── Build Dict Assembly ──────────────────────────────────────────

    def _build_dict(self) -> dict:
        """Assemble current form state into a build dict."""
        memories = []
        for slot in self._memory_slots:
            if slot.memory_name:
                memories.append(slot.to_dict())

        build = {
            "name": self._name_var.get().strip(),
            "concept": self._concept_text.get("1.0", "end-1c").strip(),
            "playstyle": self._playstyle_text.get("1.0", "end-1c").strip(),
            "_custom": True,
            "memories": memories,
        }

        strategy = self._strategy_text.get("1.0", "end-1c").strip()
        if strategy:
            build["strategy"] = strategy

        strengths = [
            s.strip() for s in
            self._strengths_text.get("1.0", "end-1c").strip().split("\n")
            if s.strip()
        ]
        if strengths:
            build["strengths"] = strengths

        weaknesses = [
            w.strip() for w in
            self._weaknesses_text.get("1.0", "end-1c").strip().split("\n")
            if w.strip()
        ]
        if weaknesses:
            build["weaknesses"] = weaknesses

        return build

    # ── Save ─────────────────────────────────────────────────────────

    def _save_build(self):
        build = self._build_dict()
        character = self._char_var.get()

        if not build["name"] or not character:
            messagebox.showwarning("Missing Info",
                                   "Please enter a build name and character.")
            return

        # Check for duplicate name in bundled builds
        char_lower = character.lower()
        for b in self.loader.builds.get(char_lower, []):
            if b["name"] == build["name"]:
                messagebox.showerror(
                    "Name Conflict",
                    f"A bundled build named '{build['name']}' already exists "
                    f"for {character}. Please choose a different name.")
                return

        # Confirm overwrite if editing
        if not self._editing_custom:
            for b in self.loader.custom_builds.get(char_lower, []):
                if b["name"] == build["name"]:
                    if not messagebox.askyesno(
                        "Overwrite?",
                        f"A custom build named '{build['name']}' already "
                        f"exists. Overwrite it?"):
                        return

        try:
            self.loader.save_custom_build(character, build)
            messagebox.showinfo(
                "Saved!",
                f"Build '{build['name']}' saved for {character}.\n"
                f"File: custom_builds/{char_lower}_builds.json")

            self._editing_custom = True
            self._delete_btn.configure(state="normal")
            self._refresh_load_dropdown()

            if self._on_build_saved:
                self._on_build_saved()

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save build:\n{e}")

    # ── Delete ───────────────────────────────────────────────────────

    def _delete_build(self):
        name = self._name_var.get().strip()
        character = self._char_var.get()
        if not name or not character:
            return

        if not messagebox.askyesno(
            "Delete Build?",
            f"Delete custom build '{name}' for {character}?"):
            return

        if self.loader.delete_custom_build(character, name):
            messagebox.showinfo("Deleted", f"Build '{name}' deleted.")
            self._clear_form()
            self._refresh_load_dropdown()
            if self._on_build_saved:
                self._on_build_saved()
        else:
            messagebox.showwarning("Not Found",
                                   "Build not found in custom builds.")

    # ── Load Existing ────────────────────────────────────────────────

    def _refresh_load_dropdown(self):
        """Rebuild the Load Existing dropdown with all builds."""
        names = []
        for char, builds in sorted(self.loader.all_builds.items()):
            for build in builds:
                prefix = "[Custom] " if build.get("_custom") else ""
                display = f"{prefix}{char.capitalize()} - {build['name']}"
                names.append(display)
        self._load_combo.configure(values=names)

    def _on_load_selected(self, _event=None):
        display = self._load_var.get()
        if not display:
            return

        # Parse display name back to character + build
        is_custom = display.startswith("[Custom] ")
        clean = display.replace("[Custom] ", "")
        parts = clean.split(" - ", 1)
        if len(parts) != 2:
            return
        char = parts[0].strip().lower()
        build_name = parts[1].strip()

        # Find the build
        build = None
        source = self.loader.all_builds
        for b in source.get(char, []):
            if b["name"] == build_name:
                build = b
                break
        if not build:
            return

        # Populate form
        self._populate_from_build(char, build, is_custom)
        self._load_var.set("")  # Reset dropdown

    def _populate_from_build(self, character: str, build: dict,
                             is_custom: bool):
        """Fill the form from an existing build dict."""
        # Set character
        char_display = character.capitalize()
        if char_display in self._char_names:
            self._char_var.set(char_display)
        else:
            # For characters that only exist in builds, not in characters.json
            self._char_var.set(char_display)

        # Build name (append copy suffix for bundled builds)
        name = build["name"]
        if not is_custom:
            name = f"{name} (Copy)"
        self._name_var.set(name)

        # Text fields
        self._concept_text.delete("1.0", "end")
        self._concept_text.insert("1.0", build.get("concept", ""))

        self._playstyle_text.delete("1.0", "end")
        self._playstyle_text.insert("1.0", build.get("playstyle", ""))

        self._strategy_text.delete("1.0", "end")
        self._strategy_text.insert("1.0", build.get("strategy", ""))

        self._strengths_text.delete("1.0", "end")
        self._strengths_text.insert(
            "1.0", "\n".join(build.get("strengths", [])))

        self._weaknesses_text.delete("1.0", "end")
        self._weaknesses_text.insert(
            "1.0", "\n".join(build.get("weaknesses", [])))

        # Memory slots - clear existing and recreate
        for slot in self._memory_slots:
            slot.destroy()
        self._memory_slots.clear()

        memories = build.get("memories", [])
        for mem in memories[:self.MAX_MEMORIES]:
            self._add_memory_slot()
            slot = self._memory_slots[-1]
            slot.set_values(
                memory_name=mem.get("name", ""),
                essences=mem.get("essences", []),
                rationale=mem.get("rationale", ""),
            )

        # If no memories, ensure at least 1 slot
        if not self._memory_slots:
            self._add_memory_slot()

        self._editing_custom = is_custom
        self._delete_btn.configure(
            state="normal" if is_custom else "disabled")

        self._update_add_btn()
        self._schedule_update()

    # ── Clear Form ───────────────────────────────────────────────────

    def _clear_form(self):
        """Reset all form fields."""
        self._char_var.set("")
        self._name_var.set("")

        for text_widget in [self._concept_text, self._playstyle_text,
                            self._strategy_text, self._strengths_text,
                            self._weaknesses_text]:
            text_widget.delete("1.0", "end")

        for slot in self._memory_slots:
            slot.destroy()
        self._memory_slots.clear()
        self._add_memory_slot()

        self._editing_custom = False
        self._delete_btn.configure(state="disabled")
        self._schedule_update()

    # ── Public API (called from other tabs) ──────────────────────────

    def load_build(self, character: str, build: dict):
        """Load a build into the creator for cloning."""
        is_custom = build.get("_custom", False)
        self._populate_from_build(character, build, is_custom)
