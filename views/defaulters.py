"""
views/defaulters.py
-------------------
Defaulters list — students with overdue installments from installment_schedules.
Month filter removed. Shows students who have unpaid/overdue installments.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date
import threading

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class DefaultersView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._build_ui()
        self._load_defaulters()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Defaulters List",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="Students with overdue installments",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 16)
        )

        # Controls bar
        ctrl = ctk.CTkFrame(
            self, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        ctrl.pack(fill="x", padx=30, pady=(0, 16))
        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(
            inner, text="📋  Showing students with OVERDUE installments",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=("#c2410c", "#fb923c"),
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            inner, text="⟳  Refresh", width=110, height=40, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._load_defaulters,
        ).pack(side="left", padx=(12, 0))

        self.lbl_count = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            text_color="#dc2626",
        )
        self.lbl_count.pack(side="right")

        # Table card
        card = ctk.CTkFrame(
            self, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        card.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        tf = ctk.CTkFrame(card, fg_color="transparent")
        tf.pack(fill="both", expand=True, padx=15, pady=15)
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Def.Treeview",
            background=NAVY_LIGHT, foreground="#f8fafc",
            rowheight=48, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 12),
        )
        style.configure(
            "Def.Treeview.Heading",
            background=NAVY, foreground="#cbd5e1",
            relief="flat", font=("Segoe UI", 13, "bold"), padding=(6, 12),
        )
        style.map(
            "Def.Treeview",
            background=[("selected", "#dc2626")],
            foreground=[("selected", "white")],
        )

        cols = ("ID", "Name", "Phone", "Course", "Inst #", "Due Date", "Amount Due", "Paid", "Remaining")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="Def.Treeview")
        for col in cols:
            self.tree.heading(col, text=col, anchor="center")
        self.tree.column("ID",          width=65,  anchor="center")
        self.tree.column("Name",        width=160, anchor="center")
        self.tree.column("Phone",       width=120, anchor="center")
        self.tree.column("Course",      width=100, anchor="center")
        self.tree.column("Inst #",      width=65,  anchor="center")
        self.tree.column("Due Date",    width=110, anchor="center")
        self.tree.column("Amount Due",  width=110, anchor="center")
        self.tree.column("Paid",        width=110, anchor="center")
        self.tree.column("Remaining",   width=110, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(
            self, text="ℹ  Students above have OVERDUE installments that are unpaid.",
            font=ctk.CTkFont(size=11), text_color=("#94a3b8", "#64748b"),
        ).pack(pady=(0, 6))

    def _load_defaulters(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            today = date.today()
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT i.id AS inst_id, i.inst_no, i.due_date,
                       i.amount_due, i.amount_paid,
                       s.id AS student_id, s.name, s.course, s.phone
                FROM installment_schedules i
                JOIN students s ON i.student_id = s.id
                WHERE i.amount_paid < i.amount_due
                  AND i.due_date < %s
                ORDER BY i.due_date ASC
            """, (today,))
            results = cursor.fetchall()
            cursor.close()
            self._render_defaulters(results)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))


    def _render_defaulters(self, results):
        count = len(results)
        self.lbl_count.configure(
            text=f"⚠  {count} overdue installment{'s' if count != 1 else ''} found"
            if count else "✔  No overdue installments!",
            text_color="#dc2626" if count else "#059669",
        )

        self.tree.tag_configure("even", background="#1e293b")
        self.tree.tag_configure("odd",  background="#0f172a")

        for i, d in enumerate(results):
            stripe = "even" if i % 2 == 0 else "odd"
            amt_due  = float(d["amount_due"])
            amt_paid = float(d["amount_paid"])
            remaining = amt_due - amt_paid
            due_date = d["due_date"]
            due_str  = due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date)

            self.tree.insert("", "end", values=(
                f"#{d['student_id']:03d}",
                d["name"],
                d.get("phone", "N/A"),
                d["course"],
                f"#{d['inst_no']}",
                due_str,
                f"₹{amt_due:,.0f}",
                f"₹{amt_paid:,.0f}",
                f"₹{remaining:,.0f}",
            ), tags=(stripe,))

    def refresh(self):
        self._load_defaulters()
