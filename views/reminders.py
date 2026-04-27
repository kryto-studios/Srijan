"""
views/reminders.py
------------------
Payment Reminder Center — Srijan Institute theme (Navy + Reddish-Orange).
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date

MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]

CURRENT_MONTH_NAME = MONTHS[date.today().month - 1]
CURRENT_DAY        = date.today().day

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class RemindersView(ctk.CTkFrame):
    badge_count: int = 0

    def __init__(self, parent, db, toast=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db    = db
        self.toast = toast
        self._notified: set[int] = set()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Payment Reminders",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="Students who haven't paid for the selected month",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkButton(
            header, text="⟳  Refresh", width=120, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self.refresh,
        ).pack(side="right")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 14)
        )

        # Info banner
        self.banner = ctk.CTkFrame(
            self, fg_color=("#fff7ed", "#431407"),
            corner_radius=12, border_width=1, border_color=ORANGE,
        )
        self.banner.pack(fill="x", padx=30, pady=(0, 14))
        bi = ctk.CTkFrame(self.banner, fg_color="transparent")
        bi.pack(fill="x", padx=18, pady=12)

        ctk.CTkLabel(
            bi, text="⚠", font=ctk.CTkFont(size=22), text_color=ORANGE,
        ).pack(side="left", padx=(0, 12))
        self.lbl_banner = ctk.CTkLabel(
            bi, text=f"Checking reminders for {CURRENT_MONTH_NAME}…",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            text_color=(ORANGE, "#fed7aa"), anchor="w",
        )
        self.lbl_banner.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            bi, text=f"Day {CURRENT_DAY} of month",
            font=ctk.CTkFont(size=11), text_color=("#b45309", "#fdba74"),
        ).pack(side="right")

        # Month selector
        sel = ctk.CTkFrame(self, fg_color="transparent")
        sel.pack(fill="x", padx=30, pady=(0, 14))
        ctk.CTkLabel(
            sel, text="Showing defaulters for:",
            font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8"),
        ).pack(side="left", padx=(0, 10))
        self.var_month = ctk.StringVar(value=CURRENT_MONTH_NAME)
        ctk.CTkOptionMenu(
            sel, values=MONTHS, variable=self.var_month,
            width=160, height=36, corner_radius=8,
            fg_color=("#f8fafc", NAVY),
            button_color=ORANGE, button_hover_color=ORANGE_HOV,
            command=lambda _: self.refresh(),
        ).pack(side="left")

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    def refresh(self, *_):
        for w in self.scroll.winfo_children():
            w.destroy()

        month = self.var_month.get()
        try:
            defaulters = self.db.get_defaulters(month)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        RemindersView.badge_count = len(defaulters)

        if not defaulters:
            self.lbl_banner.configure(
                text=f"✅  All students have paid for {month}! Great job.",
                text_color=("#065f46", "#d1fae5"),
            )
            self.banner.configure(fg_color=("#ecfdf5", "#064e3b"), border_color="#059669")
            ctk.CTkLabel(
                self.scroll,
                text="🎉  No defaulters found for this month.",
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=15),
                text_color=("#64748b", "#94a3b8"),
            ).pack(expand=True, pady=60)
            return

        self.lbl_banner.configure(
            text=f"⚠  {len(defaulters)} student{'s' if len(defaulters)>1 else ''} "
                 f"have NOT paid for {month}.",
            text_color=(ORANGE, "#fed7aa"),
        )
        self.banner.configure(fg_color=("#fff7ed", "#431407"), border_color=ORANGE)

        # Table header
        hdr = ctk.CTkFrame(self.scroll, fg_color=("#f8fafc", NAVY), corner_radius=8)
        hdr.pack(fill="x", pady=(0, 4))
        for txt, w in [("#", 55), ("Student Name", 0), ("Course", 145), ("Balance", 120), ("Status", 105), ("Action", 115)]:
            ctk.CTkLabel(
                hdr, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#64748b", "#94a3b8"),
            ).pack(side="left", padx=8, pady=10)

        for d in defaulters:
            self._add_row(d, month)

    def _add_row(self, d: dict, month: str):
        notified = d["id"] in self._notified
        row = ctk.CTkFrame(
            self.scroll,
            fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=8, border_width=1,
            border_color=("#e2e8f0", "#334155") if not notified else "#059669",
        )
        row.pack(fill="x", pady=3)

        bal       = float(d["balance"])
        bal_color = "#dc2626" if bal > 0 else "#059669"

        for val, w, color in [
            (f"#{d['id']:03d}", 55, ("#475569", "#94a3b8")),
            (d["name"],          0,  ("#0f172a", "white")),
            (d["course"],        145,("#64748b", "#94a3b8")),
            (f"₹{bal:,.0f}",    120, bal_color),
        ]:
            ctk.CTkLabel(
                row, text=val, width=w,
                font=ctk.CTkFont(size=12), text_color=color, anchor="w",
            ).pack(side="left", padx=8, pady=10)

        # Status badge
        if notified:
            badge = ctk.CTkLabel(
                row, text="✔ Notified", width=100,
                fg_color="#064e3b", corner_radius=6,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#34d399",
            )
        else:
            badge = ctk.CTkLabel(
                row, text="⚠ Pending", width=100,
                fg_color="#431407", corner_radius=6,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#fdba74",
            )
        badge.pack(side="left", padx=8)

        sid   = d["id"]
        sname = d["name"]

        def send_reminder(student_id=sid, student_name=sname):
            self._notified.add(student_id)
            if self.toast:
                self.toast.show(f"Reminder sent to {student_name} for {month}.", "warning")
            self.refresh()

        ctk.CTkButton(
            row,
            text="✓ Notified" if notified else "🔔 Remind",
            width=100, height=30, corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669" if notified else ORANGE,
            hover_color="#047857" if notified else ORANGE_HOV,
            state="disabled" if notified else "normal",
            command=send_reminder,
        ).pack(side="left", padx=8)
