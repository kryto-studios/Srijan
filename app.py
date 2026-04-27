"""
app.py
------
Main entry point — Student Fee Management System (Professional Edition).
Features: animated sidebar nav, top bar with live clock,
          startup payment reminders, toast notifications.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from PIL import Image

from database_manager import DatabaseManager
from utils.toast       import ToastManager
from utils.animator    import TransitionBar

from views.dashboard      import DashboardView
from views.add_student    import AddStudentView
from views.fee_records    import FeeRecordsView
from views.defaulters     import DefaultersView
from views.monthly_status import MonthlyStatusView
from views.reminders      import RemindersView
from views.student_directory import StudentDirectoryView


# ──────────────────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────────────────
APP_TITLE   = "Student Fee Management System — Professional"
APP_WIDTH   = 1340
APP_HEIGHT  = 820
SIDEBAR_W   = 230
TOPBAR_H    = 52
ACCENT      = "#c2410c"
ACCENT_DARK = "#9a3412"
SIDEBAR_BG  = ("#0f172a", "#020617")
TOPBAR_BG   = ("#f1f5f9", "#0f172a")
CONTENT_BG  = ("#f8fafc", "#020617")

NAV_ITEMS = [
    {"id": "dashboard",      "icon": "\uE80F", "label": "Dashboard"},
    {"id": "student_directory","icon": "\uE71C", "label": "Student Directory"},
    {"id": "add_student",    "icon": "\uE77B", "label": "Add Student"},
    {"id": "fee_records",    "icon": "\uE825", "label": "Fee Records"},
    {"id": "monthly_status", "icon": "\uE787", "label": "Monthly Status"},
    {"id": "reminders",      "icon": "\uEA8F", "label": "Reminders"},
    {"id": "defaulters",     "icon": "\uE7BA", "label": "Defaulters"},
]

PAGE_TITLES = {
    "dashboard":      ("\uE80F", "Dashboard"),
    "student_directory": ("\uE71C", "Student Directory"),
    "add_student":    ("\uE77B", "Add Student"),
    "fee_records":    ("\uE825", "Fee Records"),
    "monthly_status": ("\uE787", "Monthly Status"),
    "reminders":      ("\uEA8F", "Reminders"),
    "defaulters":     ("\uE7BA", "Defaulters"),
}


# ──────────────────────────────────────────────────────────────────────────────
#  Main Application
# ──────────────────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db           = db
        self._active_nav  = None
        self._views: dict[str, ctk.CTkFrame] = {}

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(1060, 680)

        # Open in maximized state by default (standard Windows "fullscreen")
        self.after(0, lambda: self.state('zoomed'))

        # Fullscreen key bindings
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self._build_root_layout()
        self._build_sidebar()
        self._build_topbar()
        self._build_content_area()
        self._init_views()
        self._navigate("dashboard", animated=False)

        # Startup: show reminders after 800 ms (let UI fully render first)
        self.after(800, self._check_startup_reminders)

    # ── Root Layout ───────────────────────────────────────────────────────── #

    def _build_root_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(0, minsize=TOPBAR_H)

    # ── Sidebar ───────────────────────────────────────────────────────────── #

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_W, corner_radius=0, fg_color=SIDEBAR_BG,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(99, weight=1)

        # Accent stripe
        ctk.CTkFrame(self.sidebar, height=4, fg_color=ACCENT, corner_radius=0).grid(
            row=0, column=0, sticky="ew")

        # Logo block — wide banner format
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(16, 8))

        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open("assets/logo.png"),
                dark_image=Image.open("assets/logo.png"),
                size=(210, 80)   # banner aspect ratio ~700x270
            )
            ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(pady=(8, 0))
        except Exception:
            ctk.CTkLabel(logo_frame, text="\uE835",
                         font=ctk.CTkFont(family="Segoe Fluent Icons", size=48),
                         text_color="white").pack(pady=(10, 4))
            ctk.CTkLabel(logo_frame, text="Srijan Institute",
                         font=ctk.CTkFont(family="Segoe UI Variable Display", size=16, weight="bold"),
                         text_color="white").pack()

        ctk.CTkLabel(logo_frame, text="Director: Naveen",
                     font=ctk.CTkFont(family="Segoe UI Variable Display", size=11),
                     text_color="#94a3b8").pack(pady=(4, 0))

        # Nav buttons
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._nav_notches: dict[str, ctk.CTkFrame] = {}
        self._reminder_badge: dict[str, ctk.CTkLabel] = {}

        for i, item in enumerate(NAV_ITEMS):
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=44)
            btn_frame.grid(row=i + 2, column=0, sticky="ew", padx=(15, 0), pady=4)
            btn_frame.grid_propagate(False)
            btn_frame.columnconfigure(0, weight=1)
            btn_frame.rowconfigure(0, weight=1)

            btn = ctk.CTkButton(
                btn_frame,
                text=f" \u200b {item['icon']} \u200b  {item['label']}",
                anchor="w",
                height=44,
                corner_radius=22,
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
                fg_color="transparent",
                text_color="#9da0b5",
                hover_color="#1e293b",
                command=lambda nav_id=item["id"]: self._navigate(nav_id),
            )
            btn.grid(row=0, column=0, sticky="nsew")

            notch = ctk.CTkFrame(btn_frame, width=22, corner_radius=0, fg_color="transparent")
            notch.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
            self._nav_notches[item["id"]] = notch
            self._nav_buttons[item["id"]] = btn

            # Badge label for reminders
            if item["id"] == "reminders":
                badge = ctk.CTkLabel(
                    btn_frame, text="",
                    width=24, height=20,
                    corner_radius=10,
                    fg_color="#dc2626",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="white",
                )
                badge.grid(row=0, column=1, padx=(4, 0))
                self._reminder_badge["label"] = badge

        # Divider + theme toggle
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1e293b").grid(
            row=98, column=0, sticky="ew", padx=0, pady=10)

        theme_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        theme_frame.grid(row=100, column=0, sticky="ew", padx=14, pady=(0, 20))
        ctk.CTkLabel(theme_frame, text="Appearance",
                     font=ctk.CTkFont(size=11), text_color="#475569").pack(anchor="w", pady=(0,6))
        self.theme_switch = ctk.CTkSwitch(
            theme_frame, text="Dark Mode",
            command=self._toggle_theme,
            font=ctk.CTkFont(size=12),
            progress_color=ACCENT,
            onvalue="dark", offvalue="light",
        )
        self.theme_switch.select()
        self.theme_switch.pack(anchor="w")

    # ── Top Bar ───────────────────────────────────────────────────────────── #

    def _build_topbar(self):
        self.topbar = ctk.CTkFrame(
            self, height=TOPBAR_H, corner_radius=0,
            fg_color=TOPBAR_BG,
            border_width=0,
        )
        self.topbar.grid(row=0, column=1, sticky="nsew")
        self.topbar.grid_propagate(False)
        self.topbar.columnconfigure(1, weight=1)

        # Left: page title
        self.lbl_page_title = ctk.CTkLabel(
            self.topbar, text="Welcome to Srijan Institute",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=16, weight="bold"),
            text_color=ACCENT,
            anchor="w",
        )
        self.lbl_page_title.grid(row=0, column=0, sticky="w", padx=20)

        # Right: clock + reminder button
        right_frame = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=18, pady=8)

        self.lbl_clock = ctk.CTkLabel(
            right_frame, text="Academic Year 2026 - 2027",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            text_color=(ACCENT, "#fb923c"),
        )
        self.lbl_clock.pack(side="left", padx=(0, 14))

        ctk.CTkButton(
            right_frame, text="\uEA8F Notifications", width=120, height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color=("#ffffff","#27272a"),
            text_color=ACCENT,
            hover_color=("#f4f0f7","#18181b"),
            command=lambda: self._navigate("reminders"),
        ).pack(side="left")

        # Bottom divider
        ctk.CTkFrame(self.topbar, height=1,
                     fg_color=("#e2e8f0","#27272a")).place(relx=0, rely=1.0,
                                                             anchor="sw", relwidth=1)

    # ── Content Area ──────────────────────────────────────────────────────── #

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=CONTENT_BG)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Transition bar (overlaid on top of content)
        self._transition = TransitionBar(self.content)

        # Toast manager (overlaid on content)
        self.toast = ToastManager(self.content)

    # ── Views ─────────────────────────────────────────────────────────────── #

    def _init_views(self):
        def refresh_all():
            for v in self._views.values():
                if hasattr(v, "refresh"):
                    v.refresh()
            self._update_reminder_badge()

        self._views = {
            "dashboard":      DashboardView(self.content, self.db),
            "student_directory": StudentDirectoryView(self.content, self.db),
            "add_student":    AddStudentView(self.content, self.db, on_success=refresh_all),
            "fee_records":    FeeRecordsView(self.content, self.db, toast=self.toast),
            "monthly_status": MonthlyStatusView(self.content, self.db),
            "reminders":      RemindersView(self.content, self.db, toast=self.toast),
            "defaulters":     DefaultersView(self.content, self.db),
        }
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    # ── Navigation ────────────────────────────────────────────────────────── #

    def _navigate(self, nav_id: str, animated: bool = True):
        if nav_id == self._active_nav and animated:
            return

        # Update sidebar buttons
        for key, btn in self._nav_buttons.items():
            notch = self._nav_notches[key]
            if key == nav_id:
                btn.configure(fg_color=CONTENT_BG, text_color=ACCENT, hover_color=CONTENT_BG)
                notch.configure(fg_color=CONTENT_BG)
            else:
                btn.configure(fg_color="transparent", text_color="#9da0b5", hover_color="#454060")
                notch.configure(fg_color="transparent")

        # Update top bar title
        icon, title = PAGE_TITLES.get(nav_id, ("📄", nav_id.replace("_", " ").title()))
        self.lbl_page_title.configure(text=f"{icon}  {title}")

        self._active_nav = nav_id

        if animated and nav_id in self._views:
            self._transition.animate(
                on_midpoint=lambda: self._views[nav_id].tkraise(),
                on_finish=lambda: self._trigger_refresh(nav_id)
            )
        else:
            self._views[nav_id].tkraise()
            self._trigger_refresh(nav_id)

    def _trigger_refresh(self, nav_id: str):
        if nav_id in self._views:
            if hasattr(self._views[nav_id], "refresh"):
                self._views[nav_id].refresh()
            self._update_reminder_badge()

    # ── Reminder Badge ────────────────────────────────────────────────────── #

    def _update_reminder_badge(self):
        try:
            count = RemindersView.badge_count
            badge = self._reminder_badge.get("label")
            if badge:
                if count > 0:
                    badge.configure(text=str(count))
                    badge.grid()
                else:
                    badge.grid_remove()
        except Exception:
            pass

    def _check_startup_reminders(self):
        """Show toast notifications for unpaid students on app start."""
        try:
            from datetime import date
            from views.reminders import MONTHS
            month = MONTHS[date.today().month - 1]
            defaulters = self.db.get_defaulters(month)
            RemindersView.badge_count = len(defaulters)
            self._update_reminder_badge()

            if not defaulters:
                self.toast.show(f"✅ All fees paid for {month}!", "success")
                return

            # Show up to 2 individual toasts
            for d in defaulters[:2]:
                self.after(
                    300 * (defaulters.index(d) + 1),
                    lambda name=d["name"], bal=float(d["balance"]):
                        self.toast.show(
                            f"⚠ {name} — Balance: ₹{bal:,.0f} unpaid for {month}",
                            "warning"
                        )
                )
            # Summary toast if more
            if len(defaulters) > 2:
                extra = len(defaulters) - 2
                self.after(
                    900,
                    lambda: self.toast.show(
                        f"+ {extra} more student{'s' if extra>1 else ''} have unpaid fees for {month}.",
                        "warning"
                    )
                )
        except Exception as e:
            print(f"[Startup Reminders] {e}")

    # ── Clock (Removed live clock to match static academic year UI) ── #

    # ── Theme ──────────────────────────────────────────────────────────────── #

    def _toggle_theme(self):
        mode = self.theme_switch.get()
        ctk.set_appearance_mode(mode)
        self.theme_switch.configure(text=f"{'Dark' if mode == 'dark' else 'Light'} Mode")


# ──────────────────────────────────────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────────────────────────────────────
def main():
    try:
        db = DatabaseManager()
    except ConnectionError as e:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database Connection Failed", str(e))
        root.destroy()
        return

    app = App(db)
    app.protocol("WM_DELETE_WINDOW", lambda: (db.close(), app.destroy()))
    app.mainloop()


if __name__ == "__main__":
    main()
