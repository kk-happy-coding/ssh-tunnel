"""Custom reusable widgets for SSH Tunnel Manager GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class StatusIndicator(tk.Canvas):
    """Visual status indicator widget."""

    STATUS_COLORS = {
        "disconnected": "#95a5a6",
        "connecting": "#f39c12",
        "connected": "#27ae60",
        "error": "#e74c3c",
        "reconnecting": "#3498db",
    }

    def __init__(self, parent: tk.Widget, size: int = 12, **kwargs: object) -> None:
        """
        Initialize status indicator.

        Args:
            parent: Parent widget
            size: Size of the indicator
            **kwargs: Additional canvas arguments
        """
        super().__init__(parent, width=size, height=size, highlightthickness=0, **kwargs)
        self.size = size
        self.indicator = self.create_oval(2, 2, size - 2, size - 2, fill=self.STATUS_COLORS["disconnected"])

    def set_status(self, status: str) -> None:
        """
        Set indicator status.

        Args:
            status: Status name
        """
        color = self.STATUS_COLORS.get(status.lower(), "#95a5a6")
        self.itemconfig(self.indicator, fill=color)


class ValidatedEntry(ttk.Entry):
    """Entry widget with built-in validation."""

    def __init__(
        self,
        parent: tk.Widget,
        validator: Optional[Callable[[str], tuple]] = None,
        **kwargs: object,
    ) -> None:
        """
        Initialize validated entry.

        Args:
            parent: Parent widget
            validator: Validation function returning (is_valid, error_message)
            **kwargs: Additional entry arguments
        """
        super().__init__(parent, **kwargs)
        self.validator = validator
        self.error_label: Optional[tk.Label] = None
        self.is_valid_flag = True

        # Bind validation on focus out
        self.bind("<FocusOut>", self._validate_on_focus_out)
        self.bind("<KeyRelease>", self._clear_error_on_input)

    def _validate_on_focus_out(self, event: object = None) -> None:
        """Validate entry on focus out."""
        self.validate()

    def _clear_error_on_input(self, event: object = None) -> None:
        """Clear error styling when user types."""
        if not self.is_valid_flag:
            self.configure(style="TEntry")

    def validate(self) -> bool:
        """
        Validate entry value.

        Returns:
            True if valid, False otherwise
        """
        if not self.validator:
            return True

        value = self.get()
        is_valid, error_message = self.validator(value)

        self.is_valid_flag = is_valid

        if not is_valid:
            # Show error styling
            self.configure(style="Error.TEntry")
            if self.error_label:
                self.error_label.config(text=error_message or "Invalid input")
        else:
            self.configure(style="TEntry")
            if self.error_label:
                self.error_label.config(text="")

        return is_valid

    def set_error_label(self, label: tk.Label) -> None:
        """
        Set error label for displaying validation messages.

        Args:
            label: Label widget
        """
        self.error_label = label

    def is_valid(self) -> bool:
        """Check if entry value is valid."""
        return self.validate()


class ToggleSwitch(tk.Canvas):
    """Toggle switch widget."""

    def __init__(
        self,
        parent: tk.Widget,
        width: int = 50,
        height: int = 24,
        **kwargs: object,
    ) -> None:
        """
        Initialize toggle switch.

        Args:
            parent: Parent widget
            width: Switch width
            height: Switch height
            **kwargs: Additional canvas arguments
        """
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)

        self.width = width
        self.height = height
        self.is_on = False
        self.callback: Optional[Callable] = None

        # Colors
        self.bg_on = "#4caf50"
        self.bg_off = "#cccccc"
        self.toggle_color = "#ffffff"

        # Draw switch
        radius = height / 2
        self.bg = self.create_rounded_rect(0, 0, width, height, radius, fill=self.bg_off)
        self.toggle = self.create_oval(2, 2, height - 2, height - 2, fill=self.toggle_color)

        # Bind click
        self.bind("<Button-1>", self._on_click)

    def create_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: float, **kwargs: object) -> int:
        """
        Create rounded rectangle.

        Args:
            x1, y1, x2, y2: Rectangle coordinates
            r: Corner radius
            **kwargs: Additional arguments

        Returns:
            Canvas item ID
        """
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_click(self, event: object = None) -> None:
        """Handle click event."""
        self.toggle_state()

    def toggle_state(self) -> None:
        """Toggle switch state."""
        self.is_on = not self.is_on
        self._update_visual()

        if self.callback:
            self.callback(self.is_on)

    def set_state(self, is_on: bool) -> None:
        """
        Set switch state.

        Args:
            is_on: True for on, False for off
        """
        self.is_on = is_on
        self._update_visual()

    def get_state(self) -> bool:
        """Get switch state."""
        return self.is_on

    def set_callback(self, callback: Callable) -> None:
        """
        Set callback function.

        Args:
            callback: Function to call on state change
        """
        self.callback = callback

    def _update_visual(self) -> None:
        """Update visual representation."""
        if self.is_on:
            self.itemconfig(self.bg, fill=self.bg_on)
            self.coords(self.toggle, self.width - self.height + 2, 2, self.width - 2, self.height - 2)
        else:
            self.itemconfig(self.bg, fill=self.bg_off)
            self.coords(self.toggle, 2, 2, self.height - 2, self.height - 2)


class ScrollableFrame(ttk.Frame):
    """Scrollable frame widget."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        """
        Initialize scrollable frame.

        Args:
            parent: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event: object) -> None:
        """Handle mouse wheel scrolling."""
        if hasattr(event, "delta"):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")  # type: ignore


class Tooltip:
    """Tooltip widget for displaying hints."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        """
        Initialize tooltip.

        Args:
            widget: Widget to attach tooltip to
            text: Tooltip text
        """
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[tk.Toplevel] = None

        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: object = None) -> None:
        """Show tooltip."""
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",
            foreground="#000000",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
            padx=5,
            pady=2,
        )
        label.pack()

    def hide_tooltip(self, event: object = None) -> None:
        """Hide tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
