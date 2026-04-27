"""
views/fee_records.py
--------------------
Premium Fee Records — Srijan Institute theme (Navy + Reddish-Orange).
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date

from utils import receipt_generator, exporter
from utils.fee_calculator import calculate_installments, get_overall_status, STATUS_STYLE

MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class FeeRecordsView(ctk.CTkFrame):
    def __init__(self, parent, db, toast=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db    = db
        self.toast = toast
        self._selected_student = None
        self._last_payment_id  = None
        self._current_students = []
        self._build_ui()
        self._load_students()

    # ── Build ──────────────────────────────────────────────────────────── #

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Fee Records",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="Manage student payments and installment schedules",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkButton(
            header, text="\uF1C3  Export CSV", height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color=("#1e293b", "#1e293b"), hover_color=("#334155", "#334155"),
            border_width=1, border_color=("#334155", "#475569"),
            text_color="white",
            command=self._export_csv,
        ).pack(side="right", pady=10)

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 20)
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30)
        body.columnconfigure(0, weight=6)
        body.columnconfigure(1, weight=4)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        left = ctk.CTkFrame(
            parent, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        # Search
        sf = ctk.CTkFrame(left, fg_color="transparent")
        sf.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        sf.columnconfigure(0, weight=1)
        self.var_search = ctk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._load_students())
        ctk.CTkEntry(
            sf, textvariable=self.var_search,
            placeholder_text="Search by Name or ID…",
            height=40, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#3f3f46"),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(
            sf, text="Search", width=90, height=40, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._load_students,
        ).grid(row=0, column=1)

        # Course filter
        ff = ctk.CTkFrame(left, fg_color="transparent")
        ff.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        ctk.CTkLabel(
            ff, text="Filter:", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"),
        ).pack(side="left", padx=(0, 8))
        self.var_course_filter = ctk.StringVar(value="All")
        self.opt_course = ctk.CTkOptionMenu(
            ff, values=["All"], variable=self.var_course_filter,
            width=160, height=36, corner_radius=8,
            fg_color=("#f8fafc", NAVY),
            button_color=ORANGE, button_hover_color=ORANGE_HOV,
            command=lambda _: self._load_students(),
        )
        self.opt_course.pack(side="left")

        # Treeview
        tf = ctk.CTkFrame(left, fg_color="transparent")
        tf.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Fee.Treeview",
            background=NAVY_LIGHT, foreground="#e2e8f0",
            rowheight=40, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Fee.Treeview.Heading",
            background=NAVY, foreground="#94a3b8",
            relief="flat", font=("Segoe UI", 11, "bold"), padding=(5, 10),
        )
        style.map(
            "Fee.Treeview",
            background=[("selected", ORANGE)],
            foreground=[("selected", "white")],
        )

        cols = ("ID", "Name", "Course", "Status", "Paid ₹", "Balance ₹")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="Fee.Treeview")
        self.tree.heading("ID",        text="ID",          anchor="center")
        self.tree.column ("ID",        width=65,           anchor="center")
        self.tree.heading("Name",      text="Student Name", anchor="w")
        self.tree.column ("Name",      width=175,           anchor="w")
        self.tree.heading("Course",    text="Course",       anchor="w")
        self.tree.column ("Course",    width=120,           anchor="w")
        self.tree.heading("Status",    text="Status",       anchor="center")
        self.tree.column ("Status",    width=120,           anchor="center")
        self.tree.heading("Paid ₹",   text="Total Paid",   anchor="e")
        self.tree.column ("Paid ₹",   width=110,           anchor="e")
        self.tree.heading("Balance ₹",text="Balance",      anchor="e")
        self.tree.column ("Balance ₹",width=110,           anchor="e")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_right(self, parent):
        right = ctk.CTkScrollableFrame(
            parent, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        # Student name
        self.lbl_sname = ctk.CTkLabel(
            right, text="← Select a student",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=17, weight="bold"),
            text_color=(ORANGE, "#fb923c"),
        )
        self.lbl_sname.pack(anchor="w", padx=15, pady=(15, 4))

        self.lbl_sdetail = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"), anchor="w", justify="left",
        )
        self.lbl_sdetail.pack(anchor="w", padx=15, pady=(0, 4))

        # Balance card
        bf = ctk.CTkFrame(right, fg_color=("#f8fafc", NAVY), corner_radius=10)
        bf.pack(fill="x", padx=15, pady=(8, 14))
        ctk.CTkLabel(
            bf, text="Current Balance:",
            font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8"),
        ).pack(side="left", padx=14, pady=12)
        self.lbl_balance = ctk.CTkLabel(
            bf, text="—",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=20, weight="bold"),
            text_color="#dc2626",
        )
        self.lbl_balance.pack(side="right", padx=14, pady=12)

        # Installments section
        self._section_header(right, "\uE787  Installments")
        self.installments_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.installments_frame.pack(fill="x", padx=15, pady=(0, 14))
        ctk.CTkLabel(
            self.installments_frame, text="Select a student to view installments.",
            text_color="#64748b",
        ).pack()

        # Add payment section
        self._section_header(right, "\uE710  Record Payment")

        r1 = ctk.CTkFrame(right, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(4, 8))
        r1.columnconfigure(0, weight=1)
        r1.columnconfigure(1, weight=1)

        f1 = ctk.CTkFrame(r1, fg_color="transparent")
        f1.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(
            f1, text="Amount (₹) *", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"), anchor="w",
        ).pack(fill="x")
        self.ent_amount = ctk.CTkEntry(
            f1, placeholder_text="e.g. 5000", height=38,
            corner_radius=8, border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        self.ent_amount.pack(fill="x", pady=(4, 0))

        f2 = ctk.CTkFrame(r1, fg_color="transparent")
        f2.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(
            f2, text="Month *", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"), anchor="w",
        ).pack(fill="x")
        self.var_month = ctk.StringVar(value=MONTHS[date.today().month - 1])
        ctk.CTkOptionMenu(
            f2, values=MONTHS, variable=self.var_month, height=38, corner_radius=8,
            fg_color=("#f8fafc", NAVY), button_color=ORANGE, button_hover_color=ORANGE_HOV,
        ).pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(
            right, text="Payment Date *", font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8"), anchor="w",
        ).pack(fill="x", padx=15)
        self.ent_date = ctk.CTkEntry(
            right, placeholder_text="YYYY-MM-DD", height=38,
            corner_radius=8, border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        self.ent_date.insert(0, str(date.today()))
        self.ent_date.pack(fill="x", padx=15, pady=(4, 12))

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 4))

        ctk.CTkButton(
            btn_row, text="✔  Submit", height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._submit_payment,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            btn_row, text="Pay Full Balance", height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color=NAVY_LIGHT, hover_color=NAVY,
            border_width=1, border_color="#334155",
            command=self._pay_full_balance,
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_receipt = ctk.CTkButton(
            btn_row, text="\uE8A5", height=42, corner_radius=10, width=46,
            font=ctk.CTkFont(family="Segoe Fluent Icons", size=16),
            fg_color=NAVY_LIGHT, hover_color=NAVY,
            border_width=1, border_color="#334155",
            command=self._generate_receipt, state="disabled",
        )
        self.btn_receipt.pack(side="right")

        self.lbl_pay_status = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=12), anchor="w",
        )
        self.lbl_pay_status.pack(fill="x", padx=15, pady=(4, 4))

        # History section
        self._section_header(right, "\uE81C  Payment History")
        self.history_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(
            self.history_frame, text="No payment history to display.",
            font=ctk.CTkFont(size=12), text_color=("#94a3b8", "#64748b"),
        ).pack()

    def _section_header(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w",
        ).pack(fill="x", padx=15, pady=(12, 4))
        ctk.CTkFrame(parent, height=1, fg_color=("#e2e8f0", "#27272a")).pack(
            fill="x", padx=15, pady=(0, 8)
        )

    # ── Data ───────────────────────────────────────────────────────────── #

    def _load_students(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            students = self.db.search_students(self.var_search.get(), self.var_course_filter.get())
            courses  = ["All"] + self.db.get_all_courses()
            self.opt_course.configure(values=courses)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return

        self._current_students = []
        for s in students:
            bal      = float(s["balance"])
            payments = self.db.get_payments_for_student(s["id"])
            insts    = calculate_installments(s, payments)
            status_str = get_overall_status(insts)
            s["_status"] = status_str
            sty = STATUS_STYLE.get(status_str, STATUS_STYLE["UPCOMING"])
            self._current_students.append(s)
            self.tree.insert(
                "", "end", iid=s["id"],
                values=(
                    f"#{s['id']:03d}", s["name"], s["course"],
                    f" {sty['icon']} {sty['label']} ",
                    f"₹{float(s['total_paid']):,.2f}",
                    f"₹{bal:,.2f}",
                ),
                tags=(status_str,),
            )

        for status, sty in STATUS_STYLE.items():
            self.tree.tag_configure(status, foreground=sty["color"])

    def refresh(self):
        self._load_students()

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        sid = int(sel[0].replace("#", ""))
        try:
            s = self.db.get_student_by_id(sid)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return
        if not s:
            return
        self._selected_student = s
        bal = float(s["balance"])
        self.lbl_sname.configure(text=s["name"])
        self.lbl_sdetail.configure(
            text=f"ID: #{s['id']:03d}   ·   {s['course']}   ·   {s.get('fee_frequency','Monthly')} ({s.get('course_duration_months',12)} months)\n"
                 f"Total Fee: ₹{float(s['total_course_fee']):,.2f}   ·   Paid: ₹{float(s['total_paid']):,.2f}"
        )
        self.lbl_balance.configure(
            text=f"₹{bal:,.2f}" if bal > 0 else "CLEARED ✓",
            text_color="#dc2626" if bal > 0 else "#059669",
        )
        self.lbl_pay_status.configure(text="")
        payments = self.db.get_payments_for_student(sid)
        self._render_installments(s, payments)
        self._load_history(payments)

    def _render_installments(self, student, payments):
        for w in self.installments_frame.winfo_children():
            w.destroy()
        insts = calculate_installments(student, payments)
        if not insts:
            ctk.CTkLabel(
                self.installments_frame, text="No installments calculated.",
                text_color="#64748b",
            ).pack()
            return
        for inst in insts:
            sty = STATUS_STYLE[inst["status"]]
            row = ctk.CTkFrame(
                self.installments_frame, fg_color=sty["bg"], corner_radius=6,
            )
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text=f"{inst['no']}", width=28,
                font=ctk.CTkFont(weight="bold"), text_color="white",
            ).pack(side="left", padx=6)
            ctk.CTkLabel(
                row, text=f"Due: {inst['due_date'].strftime('%b %d, %Y')}", width=108,
                font=ctk.CTkFont(size=11), text_color="#cbd5e1", anchor="w",
            ).pack(side="left", padx=6)
            ctk.CTkLabel(
                row, text=f"₹{inst['amount_due']:,.0f}", width=76,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="white", anchor="e",
            ).pack(side="left", padx=4)
            badge = ctk.CTkFrame(row, fg_color=sty["color"], corner_radius=4, height=20, width=78)
            badge.pack_propagate(False)
            badge.pack(side="right", padx=8, pady=5)
            ctk.CTkLabel(
                badge, text=sty["label"],
                font=ctk.CTkFont(size=10, weight="bold"), text_color="white",
            ).pack(expand=True, fill="both")

    def _load_history(self, payments):
        for w in self.history_frame.winfo_children():
            w.destroy()
        if not payments:
            ctk.CTkLabel(
                self.history_frame, text="No payments recorded yet.",
                font=ctk.CTkFont(size=12), text_color=("#94a3b8", "#64748b"),
            ).pack()
            return
        for p in payments:
            row = ctk.CTkFrame(self.history_frame, fg_color=("#f8fafc", NAVY), corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=p["month_name"], font=ctk.CTkFont(size=12, weight="bold"),
                width=90, anchor="w",
            ).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(
                row, text=str(p["payment_date"]), font=ctk.CTkFont(size=11),
                text_color=("#64748b", "#94a3b8"), anchor="w",
            ).pack(side="left", padx=4)
            ctk.CTkLabel(
                row, text=f"₹{float(p['amount_paid']):,.2f}",
                font=ctk.CTkFont(size=13, weight="bold"), text_color="#059669", anchor="e",
            ).pack(side="right", padx=10)
            pid = p["p_id"]
            ctk.CTkButton(
                row, text="🧾", width=32, height=28, corner_radius=6,
                fg_color=NAVY_LIGHT, hover_color=ORANGE,
                font=ctk.CTkFont(size=13),
                command=lambda p_id=pid: self._generate_receipt_for(p_id),
            ).pack(side="right", padx=4)

    # ── Payment Actions ─────────────────────────────────────────────────── #

    def _pay_full_balance(self):
        if not self._selected_student:
            self.lbl_pay_status.configure(text="⚠  Select a student first.", text_color="#dc2626")
            return
        bal = float(self._selected_student["balance"])
        if bal <= 0:
            self.lbl_pay_status.configure(text="⚠  Balance already cleared.", text_color="#059669")
            return
        self.ent_amount.delete(0, "end")
        self.ent_amount.insert(0, str(bal))
        self.lbl_pay_status.configure(
            text=f"💡  Full balance ₹{bal:,.2f} loaded. Click Submit.",
            text_color=ORANGE,
        )

    def _submit_payment(self):
        if not self._selected_student:
            self.lbl_pay_status.configure(text="⚠  Select a student first.", text_color="#dc2626")
            return
        amount_str = self.ent_amount.get().strip()
        pay_date   = self.ent_date.get().strip()
        month      = self.var_month.get()
        if not amount_str or not pay_date:
            self.lbl_pay_status.configure(text="⚠  Amount and date are required.", text_color="#dc2626")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.lbl_pay_status.configure(text="⚠  Enter a valid positive amount.", text_color="#dc2626")
            return
        try:
            sid  = self._selected_student["id"]
            p_id = self.db.add_payment(sid, amount, pay_date, month)
            self._last_payment_id = p_id
            self.lbl_pay_status.configure(
                text=f"✔  ₹{amount:,.2f} recorded for {month}.", text_color="#059669"
            )
            self.ent_amount.delete(0, "end")
            self.btn_receipt.configure(state="normal")
            if self.toast:
                self.toast.show(f"Payment of ₹{amount:,.2f} saved for {month}!", "success")
            self._load_students()
            updated = self.db.get_student_by_id(sid)
            if updated:
                self._selected_student = updated
                self._on_select()
                self.tree.selection_set(str(sid))
        except Exception as e:
            self.lbl_pay_status.configure(text=f"✖  {e}", text_color="#dc2626")

    def _generate_receipt(self):
        if not self._last_payment_id or not self._selected_student:
            return
        self._generate_receipt_for(self._last_payment_id)

    def _generate_receipt_for(self, p_id: int):
        try:
            payment = self.db.get_payment_by_id(p_id)
            if not payment:
                messagebox.showerror("Error", "Payment record not found.")
                return
            student = self.db.get_student_by_id(payment["student_id"])
            if not student:
                messagebox.showerror("Error", "Student record not found.")
                return
            fpath = receipt_generator.generate(student, payment)
            receipt_generator.open_receipt(fpath)
            if self.toast:
                self.toast.show(f"Receipt saved: {fpath.split('/')[-1]}", "info")
            self.lbl_pay_status.configure(
                text=f"🧾 Receipt: {fpath.split('/')[-1]}", text_color=ORANGE
            )
        except Exception as e:
            messagebox.showerror("Receipt Error", str(e))

    def _export_csv(self):
        if not self._current_students:
            messagebox.showinfo("Export", "No students to export.")
            return
        exporter.export_students_csv(self._current_students, parent=self)
