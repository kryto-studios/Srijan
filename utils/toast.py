"""
utils/toast.py
--------------
In-app toast notification system using CTkFrame overlays.
Supports: success, warning, error, info types.
Toasts stack vertically and auto-dismiss.
"""

import customtkinter as ctk
from typing import Literal

TOAST_COLORS = {
    "success": {"bg": "#064e3b", "border": "#059669", "icon": "✔"},
    "warning": {"bg": "#451a03", "border": "#f59e0b", "icon": "⚠"},
    "error":   {"bg": "#450a0a", "border": "#dc2626", "icon": "✖"},
    "info":    {"bg": "#1e1b4b", "border": "#4f46e5", "icon": "ℹ"},
}

TOAST_W      = 320
TOAST_H      = 64
TOAST_PAD    = 10
TOAST_DURATION = 4000   # ms before auto-dismiss
SLIDE_STEPS  = 12
SLIDE_MS     = 18


class Toast:
    """A single toast notification widget."""

    def __init__(self, manager: "ToastManager", message: str,
                 kind: str, index: int):
        self.manager = manager
        self.message = message
        self.kind    = kind
        self.index   = index          # stack position (0=lowest)
        self._alive  = True

        cfg = TOAST_COLORS.get(kind, TOAST_COLORS["info"])

        # Container frame placed over the content area
        self.frame = ctk.CTkFrame(
            manager.parent,
            width=TOAST_W, height=TOAST_H,
            corner_radius=10,
            fg_color=cfg["bg"],
            border_width=2,
            border_color=cfg["border"],
        )
        self.frame.pack_propagate(False)

        # Icon
        ctk.CTkLabel(
            self.frame,
            text=cfg["icon"],
            font=ctk.CTkFont(size=20),
            text_color=cfg["border"],
            width=40,
        ).pack(side="left", padx=(12, 4), pady=10)

        # Message
        ctk.CTkLabel(
            self.frame,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="white",
            wraplength=220,
            justify="left",
            anchor="w",
        ).pack(side="left", fill="both", expand=True, padx=(0, 8), pady=6)

        # Close button
        ctk.CTkButton(
            self.frame,
            text="✕", width=24, height=24,
            corner_radius=6,
            fg_color="transparent",
            hover_color=cfg["border"],
            text_color="white",
            font=ctk.CTkFont(size=11),
            command=self.dismiss,
        ).pack(side="right", padx=8)

        self._place()
        self._schedule_dismiss()

    def _y_pos(self) -> int:
        """Calculate Y position for this toast in the stack."""
        ph = self.manager.parent.winfo_height()
        return ph - (TOAST_H + TOAST_PAD) * (self.index + 1) - 20

    def _x_pos(self) -> int:
        pw = self.manager.parent.winfo_width()
        return pw - TOAST_W - 20

    def _place(self):
        self.frame.place(x=self._x_pos(), y=self._y_pos())
        self.frame.lift()

    def reposition(self, new_index: int):
        """Smoothly move toast to new stack position."""
        self.index = new_index
        self.frame.place(x=self._x_pos(), y=self._y_pos())

    def _schedule_dismiss(self):
        self.manager.parent.after(TOAST_DURATION, self.dismiss)

    def dismiss(self):
        if not self._alive:
            return
        self._alive = False
        try:
            self.frame.place_forget()
            self.frame.destroy()
        except Exception:
            pass
        self.manager._on_toast_dismissed(self)


class ToastManager:
    """Manages a queue of toast notifications stacked in the bottom-right."""

    def __init__(self, parent: ctk.CTkFrame):
        """
        parent: the CTkFrame that acts as the overlay surface
                (should be the content area or root window).
        """
        self.parent = parent
        self._toasts: list[Toast] = []

    def show(self, message: str,
             kind: Literal["success", "warning", "error", "info"] = "info"):
        """Display a new toast notification."""
        # Cap at 4 toasts at a time
        if len(self._toasts) >= 4:
            self._toasts[0].dismiss()

        idx   = len(self._toasts)
        toast = Toast(self, message, kind, idx)
        self._toasts.append(toast)

    def _on_toast_dismissed(self, toast: Toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
        # Re-index remaining toasts
        for i, t in enumerate(self._toasts):
            t.reposition(i)
