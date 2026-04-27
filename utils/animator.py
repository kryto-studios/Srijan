"""
utils/animator.py
-----------------
Smooth view-transition animations using a top progress bar sweep.
Works entirely with CustomTkinter's after() scheduler — no threads.
"""

import customtkinter as ctk


class TransitionBar:
    """
    A thin progress bar that sweeps across the top of the content
    area to signal a view change.  Fast (300 ms total) and non-blocking.
    """

    BAR_H    = 3
    STEPS    = 20
    INTERVAL = 14   # ms per step  →  14 × 20 = 280 ms total

    def __init__(self, parent: ctk.CTkFrame):
        self.parent  = parent
        self._bar    = ctk.CTkProgressBar(
            parent,
            height=self.BAR_H,
            corner_radius=0,
            progress_color="#c2410c",
            fg_color=("#f1f5f9", "#18181b"),
            border_width=0,
        )
        self._bar.set(0)
        self._running = False

    def animate(self, on_midpoint=None, on_finish=None):
        """
        Sweep from 0 → 1.  Calls `on_midpoint()` when bar is half-way
        (ideal moment to raise the new view behind the bar).
        Calls `on_finish()` when done.
        """
        if self._running:
            return
        self._running   = True
        self._step      = 0
        self._midpoint  = on_midpoint
        self._finish_cb = on_finish
        self._bar.place(relx=0, rely=0, relwidth=1)
        self._bar.lift()
        self._tick()

    def _tick(self):
        self._step += 1
        progress = self._step / self.STEPS
        self._bar.set(progress)

        # Fire midpoint callback at 50%
        if self._step == self.STEPS // 2 and self._midpoint:
            try:
                self._midpoint()
            except Exception:
                pass

        if self._step < self.STEPS:
            self.parent.after(self.INTERVAL, self._tick)
        else:
            self._finish()

    def _finish(self):
        self._running = False
        self._bar.place_forget()
        self._bar.set(0)
        if self._finish_cb:
            try:
                self._finish_cb()
            except Exception:
                pass
