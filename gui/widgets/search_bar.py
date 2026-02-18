"""Search bar with clear button and callback."""

import ttkbootstrap as ttk


class SearchBar(ttk.Frame):
    """Search entry with clear button. Calls on_change(query) on keypress."""

    def __init__(self, parent, placeholder: str = "Search...", on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change

        self._var = ttk.StringVar()
        self._var.trace_add("write", self._notify)

        self._entry = ttk.Entry(self, textvariable=self._var, width=30)
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._entry.insert(0, "")

        self._clear_btn = ttk.Button(self, text="X", width=3,
                                     bootstyle="secondary-outline",
                                     command=self.clear)
        self._clear_btn.pack(side="left")

        # Placeholder
        self._placeholder = placeholder
        self._show_placeholder()
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        if not self._var.get():
            self._is_placeholder = True
            self._entry.configure(foreground="#484F58")
            self._entry.delete(0, "end")
            self._entry.insert(0, self._placeholder)

    def _on_focus_in(self, _event=None):
        if getattr(self, "_is_placeholder", False):
            self._entry.delete(0, "end")
            self._entry.configure(foreground="")
            self._is_placeholder = False

    def _on_focus_out(self, _event=None):
        if not self._var.get():
            self._show_placeholder()

    def _notify(self, *_args):
        if self._on_change and not getattr(self, "_is_placeholder", False):
            self._on_change(self._var.get())

    def clear(self):
        self._entry.delete(0, "end")
        self._is_placeholder = False
        if self._on_change:
            self._on_change("")

    @property
    def query(self) -> str:
        if getattr(self, "_is_placeholder", False):
            return ""
        return self._var.get()
