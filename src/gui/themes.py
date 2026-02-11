"""Theme definitions for SSH Tunnel Manager GUI."""

from typing import Dict

# Light theme colors
LIGHT_THEME = {
    "bg": "#ffffff",
    "fg": "#000000",
    "select_bg": "#0078d7",
    "select_fg": "#ffffff",
    "button_bg": "#e1e1e1",
    "button_fg": "#000000",
    "button_active_bg": "#0078d7",
    "entry_bg": "#ffffff",
    "entry_fg": "#000000",
    "entry_disabled_bg": "#f0f0f0",
    "frame_bg": "#f5f5f5",
    "text_bg": "#ffffff",
    "text_fg": "#000000",
    "error_fg": "#d32f2f",
    "success_fg": "#388e3c",
    "warning_fg": "#f57c00",
    "info_fg": "#1976d2",
    "border": "#cccccc",
    "highlight": "#0078d7",
}

# Dark theme colors
DARK_THEME = {
    "bg": "#2b2b2b",
    "fg": "#ffffff",
    "select_bg": "#0078d7",
    "select_fg": "#ffffff",
    "button_bg": "#3c3c3c",
    "button_fg": "#ffffff",
    "button_active_bg": "#0078d7",
    "entry_bg": "#3c3c3c",
    "entry_fg": "#ffffff",
    "entry_disabled_bg": "#2b2b2b",
    "frame_bg": "#252525",
    "text_bg": "#1e1e1e",
    "text_fg": "#ffffff",
    "error_fg": "#f44336",
    "success_fg": "#4caf50",
    "warning_fg": "#ff9800",
    "info_fg": "#2196f3",
    "border": "#3c3c3c",
    "highlight": "#0078d7",
}


def get_theme(theme_name: str) -> Dict[str, str]:
    """
    Get theme color dictionary.

    Args:
        theme_name: Theme name ("light" or "dark")

    Returns:
        Dictionary of theme colors
    """
    if theme_name.lower() == "dark":
        return DARK_THEME.copy()
    return LIGHT_THEME.copy()


def apply_theme_to_widget(widget: object, theme: Dict[str, str]) -> None:
    """
    Apply theme colors to a widget.

    Args:
        widget: Tkinter widget
        theme: Theme color dictionary
    """
    try:
        if hasattr(widget, "configure"):
            widget_type = widget.winfo_class()

            if widget_type in ("Frame", "Labelframe"):
                widget.configure(bg=theme["frame_bg"])
            elif widget_type == "Label":
                widget.configure(bg=theme["bg"], fg=theme["fg"])
            elif widget_type in ("Button", "TButton"):
                widget.configure(bg=theme["button_bg"], fg=theme["button_fg"])
            elif widget_type in ("Entry", "TEntry"):
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"])
            elif widget_type == "Text":
                widget.configure(bg=theme["text_bg"], fg=theme["text_fg"])
            elif widget_type in ("Listbox", "Treeview"):
                widget.configure(bg=theme["bg"], fg=theme["fg"])

        # Recursively apply to children
        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                apply_theme_to_widget(child, theme)

    except Exception:
        pass  # Silently skip widgets that don't support theming
