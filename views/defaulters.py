"""
views/defaulters.py
-------------------
Defaulters list — Srijan Institute theme (Navy + Reddish-Orange).
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date

MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]

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
            title_f, text="Students with no payment recorded for the selected month",
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
            inner, text="Check defaulters for:",
            font=ctk.CTkFont(size=13), text_color=("#64748b", "#94a3b8"),
        ).pack(side="left", padx=(0, 12))

        self.var_month = ctk.StringVar(value=MONTHS[date.today().month - 1])
        ctk.CTkOptionMenu(
            inner, values=MONTHS, variable=self.var_month,
            width=180, height=40, corner_radius=8,
            fg_color=("#f8fafc", NAVY),
            button_color=ORANGE, button_hover_color=ORANGE_HOV,
            command=lambda _: self._load_defaulters(),
        ).pack(side="left")

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
            background=NAVY_LIGHT, foreground="#e2e8f0",
            rowheight=36, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Def.Treeview.Heading",
            background=NAVY, foreground="#94a3b8",
            relief="flat", font=("Segoe UI", 11, "bold"), padding=(6, 10),
        )
        style.map(
            "Def.Treeview",
            background=[("selected", "#dc2626")],
            foreground=[("selected", "white")],
        )

        cols = ("ID", "Name", "Father's Name", "Course", "Total Fee", "Paid", "Balance")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="Def.Treeview")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID",            width=60,  anchor="center")
        self.tree.column("Name",          width=170, anchor="w")
        self.tree.column("Father's Name", width=150, anchor="w")
        self.tree.column("Course",        width=130, anchor="w")
        self.tree.column("Total Fee",     width=120, anchor="e")
        self.tree.column("Paid",          width=120, anchor="e")
        self.tree.column("Balance",       width=120, anchor="e")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(
            self, text="ℹ  Students above have made NO payment for the selected month.",
            font=ctk.CTkFont(size=11), text_color=("#94a3b8", "#64748b"),
        ).pack(pady=(0, 6))

    def _load_defaulters(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)
        month = self.var_month.get()
        try:
            defaulters = self.db.get_defaulters(month)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        count = len(defaulters)
        self.lbl_count.configure(
            text=f"⚠  {count} defaulter{'s' if count != 1 else ''} found"
            if count else "✔  No defaulters this month!",
            text_color="#dc2626" if count else "#059669",
        )
        for d in defaulters:
            bal = float(d["balance"])
            self.tree.insert("", "end", values=(
                f"#{d['id']:03d}", d["name"], d["father_name"], d["course"],
                f"₹{float(d['total_course_fee']):,.2f}",
                f"₹{float(d['total_paid']):,.2f}",
                f"₹{bal:,.2f}",
            ))

    def refresh(self):
        self._load_defaulters()
