"""
utils/animator.py
-----------------
Smooth view-transition animations using a top progress bar sweep.
Works entirely with CustomTkinter's after() scheduler — no threads.
"""

import customtkinter as ctk
import math

def cubic_bezier_ease_in_out(t: float) -> float:
    """
    Approximation of CSS cubic-bezier(0.4, 0.0, 0.2, 1) for an Apple-like smooth feel.
    """
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - math.pow(-2 * t + 2, 3) / 2

class TransitionBar:
    """
    Fluid Wiping Animator to provide a seamless 'SPA' cross-fade feel.
    Uses sub-pixel mathematical easing and a 60FPS tick interval 
    to mask any Cumulative Layout Shift (CLS) during section switches.
    """

    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent
        # The curtain acts as the hardware-accelerated overlay mask
        self.curtain = ctk.CTkFrame(
            parent, 
            fg_color="#0f172a", 
            corner_radius=0, 
            border_width=0
        )
        self._running = False

    def animate(self, on_midpoint=None, on_finish=None):
        if self._running:
            return
        self._running = True
        self.on_midpoint = on_midpoint
        self.on_finish = on_finish
        
        self.step = 0
        self.total_steps = 30  # 30 steps @ ~16ms interval = ~480ms (60 FPS)
        self.interval = 16     # 16ms target for 60+ FPS rendering loop

        # Start off-screen
        self.curtain.place(relx=0, rely=0, relwidth=0, relheight=1)
        self.curtain.lift()
        
        self._tick_in()

    def _tick_in(self):
        self.step += 1
        t = self.step / (self.total_steps / 2)
        if t > 1.0: t = 1.0
        
        # Apply Apple-like Easing
        eased_w = cubic_bezier_ease_in_out(t)
        self.curtain.place_configure(relwidth=eased_w)
        
        if self.step < (self.total_steps // 2):
            self.parent.after(self.interval, self._tick_in)
        else:
            # Mask is fully covering the screen -> Swap layouts instantly
            if self.on_midpoint:
                try: self.on_midpoint()
                except: pass
            
            # Immediately begin transitioning out
            self.parent.after(self.interval, self._tick_out)

    def _tick_out(self):
        self.step += 1
        t = (self.step - (self.total_steps // 2)) / (self.total_steps / 2)
        if t > 1.0: t = 1.0
        
        eased_w = 1.0 - cubic_bezier_ease_in_out(t)
        
        # Slide out to the right smoothly
        self.curtain.place_configure(relx=1.0 - eased_w, relwidth=eased_w)
        
        if self.step < self.total_steps:
            self.parent.after(self.interval, self._tick_out)
        else:
            self._finish()

    def _finish(self):
        self._running = False
        self.curtain.place_forget()
        if self.on_finish:
            try: self.on_finish()
            except: pass
