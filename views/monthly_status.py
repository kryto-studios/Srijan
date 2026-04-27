"""
views/monthly_status.py
-----------------------
12-month payment calendar — Srijan Institute theme (Navy + Reddish-Orange).
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date

MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]

CURRENT_MONTH = date.today().month
CURRENT_YEAR  = date.today().year

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class MonthlyStatusView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._selected_student = None
        self._build_ui()
        self._load_students()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Monthly Status",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="12-month payment calendar per student",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text=f"Academic Year {CURRENT_YEAR}",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            text_color=(ORANGE, "#fb923c"),
        ).pack(side="right")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 20)
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=7)
        body.rowconfigure(0, weight=1)

        self._build_student_list(body)
        self._build_calendar_panel(body)

    def _build_student_list(self, parent):
        left = ctk.CTkFrame(
            parent, fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=14, border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        self.var_search = ctk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._load_students())
        ctk.CTkEntry(
            left, textvariable=self.var_search,
            placeholder_text="\uE721  Search student…",
            height=40, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

        tf = ctk.CTkFrame(left, fg_color="transparent")
        tf.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "MS.Treeview",
            background=NAVY_LIGHT, foreground="#e2e8f0",
            rowheight=32, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "MS.Treeview.Heading",
            background=NAVY, foreground="#94a3b8",
            relief="flat", font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "MS.Treeview",
            background=[("selected", ORANGE)],
            foreground=[("selected", "white")],
        )

        self.tree = ttk.Treeview(
            tf, columns=("ID", "Name", "Course"), show="headings", style="MS.Treeview"
        )
        for col, w in [("ID", 50), ("Name", 130), ("Course", 110)]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="w" if col != "ID" else "center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_calendar_panel(self, parent):
        right = ctk.CTkScrollableFrame(
            parent, fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=14, border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        self.lbl_name = ctk.CTkLabel(
            right, text="← Select a student to view their payment calendar",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w",
        )
        self.lbl_name.pack(fill="x", padx=20, pady=(18, 4))

        self.lbl_summary = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"), anchor="w",
        )
        self.lbl_summary.pack(fill="x", padx=20, pady=(0, 8))

        # Legend
        legend = ctk.CTkFrame(right, fg_color="transparent")
        legend.pack(fill="x", padx=20, pady=(0, 16))
        for color, label in [
            ("#059669", "Paid"),
            ("#dc2626", "Unpaid (Past)"),
            ("#334155", "Upcoming"),
            (ORANGE,    "Due Now"),
        ]:
            dot = ctk.CTkFrame(legend, width=12, height=12, fg_color=color, corner_radius=6)
            dot.pack(side="left", padx=(0, 4))
            ctk.CTkLabel(
                legend, text=label,
                font=ctk.CTkFont(size=11), text_color=("#64748b", "#94a3b8"),
            ).pack(side="left", padx=(0, 16))

        # Calendar grid
        self.grid_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._month_cards: list[dict] = []
        for i, month in enumerate(MONTHS):
            row_i = i // 4
            col_i = i % 4
            self.grid_frame.columnconfigure(col_i, weight=1)
            card = self._make_month_card(self.grid_frame, month, row_i, col_i)
            self._month_cards.append(card)

    def _make_month_card(self, parent, month: str, row: int, col: int) -> dict:
        frame = ctk.CTkFrame(
            parent, corner_radius=12,
            fg_color=("#f8fafc", NAVY_LIGHT),
            border_width=2, border_color=("#e2e8f0", "#334155"),
        )
        frame.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        parent.rowconfigure(row, weight=1)

        ctk.CTkLabel(
            frame, text=month[:3].upper(),
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8"),
        ).pack(pady=(12, 2))

        icon_lbl = ctk.CTkLabel(frame, text="—", font=ctk.CTkFont(size=22))
        icon_lbl.pack()

        amt_lbl = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=11), text_color=("#64748b", "#94a3b8"),
        )
        amt_lbl.pack(pady=(2, 12))

        return {"frame": frame, "icon": icon_lbl, "amt": amt_lbl, "month": month}

    # ── Data ───────────────────────────────────────────────────────────── #

    def _load_students(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            students = self.db.search_students(self.var_search.get(), "All")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        for s in students:
            self.tree.insert("", "end", iid=s["id"],
                             values=(f"#{s['id']:03d}", s["name"], s["course"]))

    def refresh(self):
        self._load_students()
        if self._selected_student:
            self._update_calendar(self._selected_student["id"])

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        sid = int(sel[0].lstrip("#"))
        try:
            s = self.db.get_student_by_id(sid)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        if not s:
            return
        self._selected_student = s
        self.lbl_name.configure(text=f"📅  {s['name']}  (ID: #{s['id']:03d})")
        self.lbl_summary.configure(
            text=f"Course: {s['course']}   ·   Fee: ₹{float(s['total_course_fee']):,.2f}"
                 f"   ·   Paid: ₹{float(s['total_paid']):,.2f}"
                 f"   ·   Balance: ₹{float(s['balance']):,.2f}"
        )
        self._update_calendar(sid)

    def _update_calendar(self, student_id: int):
        try:
            status = self.db.get_monthly_status(student_id, CURRENT_YEAR)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        for i, card in enumerate(self._month_cards):
            month_num  = i + 1
            month_name = card["month"]
            paid       = status.get(month_name, 0.0)

            if paid > 0:
                card["frame"].configure(border_color="#059669", fg_color=("#ecfdf5", "#064e3b"))
                card["icon"].configure(text="✅", text_color="#059669")
                card["amt"].configure(text=f"₹{paid:,.0f}", text_color="#059669")
            elif month_num > CURRENT_MONTH:
                card["frame"].configure(border_color="#334155", fg_color=("#f1f5f9", "#0f172a"))
                card["icon"].configure(text="🔒", text_color="#475569")
                card["amt"].configure(text="Upcoming", text_color="#475569")
            elif month_num == CURRENT_MONTH:
                card["frame"].configure(border_color=ORANGE, fg_color=("#fff7ed", "#431407"))
                card["icon"].configure(text="⏰", text_color=ORANGE)
                card["amt"].configure(text="Due Now", text_color=ORANGE)
            else:
                card["frame"].configure(border_color="#dc2626", fg_color=("#fef2f2", "#450a0a"))
                card["icon"].configure(text="❌", text_color="#dc2626")
                card["amt"].configure(text="Unpaid", text_color="#dc2626")
