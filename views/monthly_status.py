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

        header_f = ctk.CTkFrame(right, fg_color="transparent")
        header_f.pack(fill="x", padx=20, pady=(18, 4))
        
        info_f = ctk.CTkFrame(header_f, fg_color="transparent")
        info_f.pack(side="left", fill="x", expand=True)

        self.lbl_name = ctk.CTkLabel(
            info_f, text="← Select a student to view their payment status",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w",
        )
        self.lbl_name.pack(fill="x", pady=(0, 4))

        self.lbl_summary = ctk.CTkLabel(
            info_f, text="", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"), anchor="w",
        )
        self.lbl_summary.pack(fill="x", pady=(0, 8))

        # Action Buttons
        self.btn_remind = ctk.CTkButton(
            header_f, text="💬 Send WhatsApp Reminder",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            fg_color="#10b981", hover_color="#059669",
            command=self._send_reminder
        )
        self.btn_remind.pack(side="right", padx=(10, 0))
        # Hide it initially until a student is selected
        self.btn_remind.pack_forget()

        # Installments vertical list container
        self.grid_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

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
        payments = self.db.get_payments_for_student(sid)
        from utils.fee_calculator import calculate_installments
        insts = calculate_installments(s, payments)
        
        self.lbl_name.configure(text=f"📅  {s['name']}  (ID: #{s['id']:03d})")
        self.lbl_summary.configure(
            text=f"Course Type: {s.get('course_type', 'Annual')}   ·   Total Installments: {len(insts)}\n"
                 f"Fee: ₹{float(s['total_course_fee']):,.2f}   ·   Paid: ₹{float(s['total_paid']):,.2f}"
                 f"   ·   Balance: ₹{float(s['balance']):,.2f}"
        )
        self.btn_remind.pack(side="right", padx=(10, 0))
        self._update_calendar(insts)

    def _send_reminder(self):
        if not hasattr(self, '_selected_student') or not self._selected_student:
            return
            
        import urllib.parse
        import webbrowser
        from tkinter import messagebox
        
        s = self._selected_student
        name = s['name']
        phone = s.get('phone', '')
        if not phone:
            messagebox.showwarning("Warning", "No phone number available for this student.")
            return
            
        clean_phone = "".join(c for c in phone if c.isdigit() or c == "+")
        if not clean_phone.startswith("+"):
            if len(clean_phone) == 10:
                clean_phone = "+91" + clean_phone
            else:
                clean_phone = "+" + clean_phone
                
        # Find the first due month up to current month
        try:
            status = self.db.get_monthly_status(s['id'], CURRENT_YEAR)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
            
        due_month = ""
        for i, m in enumerate(MONTHS):
            if i + 1 <= CURRENT_MONTH:
                if status.get(m, 0) <= 0:
                    due_month = m
                    break
                    
        if not due_month:
            due_month = MONTHS[CURRENT_MONTH-1] # Default to current month if no distinct unpaid month found
            
        msg = (
            f"Hello {name},\n\n"
            f"This is a friendly reminder from Srijan Institute that your fee for the month of *{due_month} {CURRENT_YEAR}* is due.\n\n"
            f"Please clear your dues at the earliest.\n\n"
            f"Thank you!"
        )
        
        encoded = urllib.parse.quote(msg)
        url = f"https://wa.me/{clean_phone.replace('+','')}?text={encoded}"
        webbrowser.open(url)

    def _update_calendar(self, insts):
        from utils.fee_calculator import STATUS_STYLE

        for w in self.grid_frame.winfo_children():
            w.destroy()
            
        if not insts:
            ctk.CTkLabel(
                self.grid_frame, text="No installments calculated.",
                text_color="#64748b",
            ).pack()
            return
            
        for inst in insts:
            sty = STATUS_STYLE[inst["status"]]
            card = ctk.CTkFrame(
                self.grid_frame, corner_radius=12, height=85,
                fg_color=("#ffffff", NAVY_LIGHT), border_width=1, border_color=("#e2e8f0", "#334155")
            )
            card.pack(fill="x", pady=8, padx=10)
            card.pack_propagate(False)
            
            # Left side: Date and Info
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=24, pady=10)
            
            ctk.CTkLabel(
                left, text=f"Installment {inst['no']}",
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold"),
                text_color=("#0f172a", "white")
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                left, text=f"Due Date: {inst['due_date'].strftime('%B %d, %Y')}",
                font=ctk.CTkFont(size=13), text_color=("#64748b", "#94a3b8")
            ).pack(anchor="w", pady=(2, 0))
            
            # Middle: Amount
            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(side="left", expand=True, fill="x", padx=20)
            
            ctk.CTkLabel(
                mid, text=f"₹{inst['amount_due']:,.2f}",
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"),
                text_color=("#0f172a", "white")
            ).pack(anchor="w")
            
            # Right side: Status Badge
            # Determine background dynamically based on appearance mode (simple heuristic)
            bg_color = sty["bg"]
            
            badge = ctk.CTkFrame(card, fg_color=bg_color, corner_radius=8, height=36, width=130)
            badge.pack_propagate(False)
            badge.pack(side="right", padx=24)
            
            ctk.CTkLabel(
                badge, text=f"{sty['icon']}  {sty['label']}",
                font=ctk.CTkFont(size=13, weight="bold"), text_color=sty.get("color", "white")
            ).pack(expand=True, fill="both")
