"""
views/reminders.py
------------------
Payment Reminder Center — shows students with overdue/due-soon installments.
Month filter removed. Based on installment_schedules table.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"

# Keep MONTHS exported so app.py badge_count logic doesn't break
MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]


class RemindersView(ctk.CTkFrame):
    badge_count: int = 0

    def __init__(self, parent, db, toast=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db    = db
        self.toast = toast
        self._notified: set = set()
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
            title_f, text="Students with overdue or upcoming installments",
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
            bi, text="Checking due installments…",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            text_color=(ORANGE, "#fed7aa"), anchor="w",
        )
        self.lbl_banner.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            bi, text=f"Today: {date.today().strftime('%d %b %Y')}",
            font=ctk.CTkFont(size=11), text_color=("#b45309", "#fdba74"),
        ).pack(side="right")

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    def refresh(self, *_):
        for w in self.scroll.winfo_children():
            w.destroy()

        today = date.today()
        in_7  = today + timedelta(days=7)

        try:
            # Fetch students with overdue/due-soon installments
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT i.id AS inst_id, i.inst_no, i.due_date, i.amount_due, i.amount_paid,
                       s.id AS student_id, s.name, s.course, s.phone
                FROM installment_schedules i
                JOIN students s ON i.student_id = s.id
                WHERE i.amount_paid < i.amount_due
                  AND i.due_date <= %s
                ORDER BY i.due_date ASC
            """, (in_7,))
            due_rows = cursor.fetchall()
            cursor.close()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load reminders: {e}")
            return

        RemindersView.badge_count = len(due_rows)

        if not due_rows:
            self.lbl_banner.configure(
                text="✅  No overdue or upcoming installments! All clear.",
                text_color=("#065f46", "#d1fae5"),
            )
            self.banner.configure(fg_color=("#ecfdf5", "#064e3b"), border_color="#059669")
            ctk.CTkLabel(
                self.scroll,
                text="🎉  No pending installments found.",
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=15),
                text_color=("#64748b", "#94a3b8"),
            ).pack(expand=True, pady=60)
            return

        self.lbl_banner.configure(
            text=f"⚠  {len(due_rows)} installment{'s' if len(due_rows) > 1 else ''} "
                 f"are due or overdue.",
            text_color=(ORANGE, "#fed7aa"),
        )
        self.banner.configure(fg_color=("#fff7ed", "#431407"), border_color=ORANGE)

        for row in due_rows:
            self._add_row(row, today)

    def _add_row(self, d: dict, today: date):
        due_date = d["due_date"]
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date[:10])

        remaining = float(d["amount_due"]) - float(d["amount_paid"])
        is_overdue = due_date < today
        notified = d["inst_id"] in self._notified

        status_color = "#ef4444" if is_overdue else "#f97316"
        status_text  = "OVERDUE" if is_overdue else "DUE SOON"

        row = ctk.CTkFrame(
            self.scroll,
            fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=12, border_width=1,
            border_color=(status_color if not notified else "#059669"),
        )
        row.pack(fill="x", pady=6, padx=4)
        row.columnconfigure(1, weight=1)

        # Status badge
        badge_f = ctk.CTkFrame(row, fg_color=status_color if not notified else "#059669",
            corner_radius=8, width=80, height=28)
        badge_f.pack_propagate(False)
        badge_f.grid(row=0, column=0, padx=(12, 8), pady=16)
        ctk.CTkLabel(badge_f, text="✔ Notified" if notified else status_text,
            font=ctk.CTkFont(size=10, weight="bold"), text_color="white").pack(expand=True)

        # Name & info
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", padx=8, pady=12)
        ctk.CTkLabel(
            info, text=d["name"],
            font=ctk.CTkFont(size=14, weight="bold"), text_color=("#0f172a", "white")
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f"{d['course']}  ·  Inst #{d['inst_no']}  ·  Due: {due_date.strftime('%d %b %Y')}  ·  📞 {d.get('phone', 'N/A')}",
            font=ctk.CTkFont(size=11), text_color=("#64748b", "#94a3b8")
        ).pack(anchor="w")

        # Remaining amount
        ctk.CTkLabel(
            row, text=f"₹{remaining:,.0f}", width=100,
            font=ctk.CTkFont(size=16, weight="bold"), text_color=status_color, anchor="e",
        ).grid(row=0, column=2, padx=12, pady=16)

        # Remind button
        inst_id   = d["inst_id"]
        sname     = d["name"]

        def send_reminder(iid=inst_id, student_name=sname):
            self._notified.add(iid)
            if self.toast:
                self.toast.show(f"Reminder noted for {student_name}.", "warning")
            self.refresh()

        ctk.CTkButton(
            row,
            text="✓ Noted" if notified else "🔔 Remind",
            width=100, height=36, corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669" if notified else ORANGE,
            hover_color="#047857" if notified else ORANGE_HOV,
            state="disabled" if notified else "normal",
            command=send_reminder,
        ).grid(row=0, column=3, padx=(8, 16), pady=16)
