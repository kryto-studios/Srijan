"""
views/installment_status.py
----------------------------
Installment Status + Manager — per-row payment control with history.
Double-click or click Pay button to record Full / Partial / Delay.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date, timedelta
import threading

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"

STATUS_CFG = {
    "PAID":     {"color": "#10b981", "label": "✔ PAID"},
    "PARTIAL":  {"color": "#f97316", "label": "◑ PARTIAL"},
    "OVERDUE":  {"color": "#ef4444", "label": "✖ OVERDUE"},
    "DUE SOON": {"color": "#eab308", "label": "⚠ DUE SOON"},
    "UPCOMING": {"color": "#3b82f6", "label": "● UPCOMING"},
}


# ── Payment Dialog ──────────────────────────────────────────────────────── #

class PaymentDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, inst_row, on_done):
        super().__init__(parent)
        self.db       = db
        self.inst     = inst_row
        self.on_done  = on_done

        self.title(f"Record Payment — {inst_row['name']} Inst #{inst_row['inst_no']}")
        self.geometry("440x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=NAVY)
        self._build()

    def _build(self):
        try:
            inst = self.inst
            due  = float(inst["amount_due"])
            paid = float(inst["amount_paid"])
            rem  = max(0, due - paid)

            ctk.CTkLabel(self, text=f"  {inst['name']}",
                font=ctk.CTkFont(size=16, weight="bold"), text_color="white", anchor="w",
            ).pack(fill="x", padx=20, pady=(18, 2))
            student = self.db.get_student_by_id(inst['student_id'])

            # Calculate full installment breakdown
            all_insts = self.db.get_installments(inst['student_id'])
            c_paid    = sum(1 for i in all_insts if i["status"] == "PAID")
            c_overdue = sum(1 for i in all_insts if i["status"] == "OVERDUE")
            c_pending = len(all_insts) - c_paid - c_overdue

            if student:
                total_paid   = float(student.get('total_paid', 0))
                bal          = float(student.get('balance', 0))
                summary_text = f"Total Paid: ₹{total_paid:,.0f}  |  Balance Left: ₹{bal:,.0f}"
            else:
                summary_text = ""

            ctk.CTkLabel(self,
                text=f"  {inst['course']}  ·  Inst #{inst['inst_no']}  ·  Due: {inst['_due_str']}",
                font=ctk.CTkFont(size=11), text_color="#94a3b8", anchor="w",
            ).pack(fill="x", padx=20, pady=(0, 4))

            if summary_text:
                ctk.CTkLabel(self, text=f"  {summary_text}",
                    font=ctk.CTkFont(size=11), text_color="#64748b", anchor="w",
                ).pack(fill="x", padx=20, pady=(0, 4))

            # Installment breakdown chips
            bd_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
            bd_frame.pack(fill="x", padx=20, pady=(0, 10))
            chips = [
                (f"Total: {len(all_insts)}", "white"),
                (f"✔ Paid: {c_paid}",        "#10b981"),
                (f"● Pending: {c_pending}",  "#f97316"),
            ]
            if c_overdue > 0:
                chips.append((f"✖ Overdue: {c_overdue}", "#ef4444"))
            for txt, clr in chips:
                ctk.CTkLabel(bd_frame, text=txt,
                    font=ctk.CTkFont(size=11, weight="bold"), text_color=clr,
                ).pack(side="left", padx=12, pady=8)

            # This-installment info bar
            bar = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=8)
            bar.pack(fill="x", padx=20, pady=(0, 10))
            for lbl, val, clr in [
                ("This Inst. Due", f"₹{due:,.0f}",  "white"),
                ("Paid So Far",    f"₹{paid:,.0f}", "#10b981"),
                ("Remaining",      f"₹{rem:,.0f}",  "#f97316"),
            ]:
                col = ctk.CTkFrame(bar, fg_color="transparent")
                col.pack(side="left", expand=True, padx=10, pady=10)
                ctk.CTkLabel(col, text=lbl, font=ctk.CTkFont(size=10),
                    text_color="#64748b").pack()
                ctk.CTkLabel(col, text=val, font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=clr).pack()

            # Mode selector
            ctk.CTkLabel(self, text="Payment Mode:", font=ctk.CTkFont(size=12),
                text_color="#94a3b8", anchor="w").pack(fill="x", padx=20, pady=(0, 4))
            self.var_mode = ctk.StringVar(value="Full")
            mode_f = ctk.CTkFrame(self, fg_color="transparent")
            mode_f.pack(fill="x", padx=20, pady=(0, 10))
            for m in ["Full", "Partial", "Delay"]:
                ctk.CTkRadioButton(mode_f, text=m, variable=self.var_mode, value=m,
                    font=ctk.CTkFont(size=12), text_color="white",
                    fg_color=ORANGE, hover_color=ORANGE_HOV,
                    command=self._on_mode_change,
                ).pack(side="left", padx=(0, 18))

            # Amount entry
            amt_f = ctk.CTkFrame(self, fg_color="transparent")
            amt_f.pack(fill="x", padx=20, pady=(0, 8))
            ctk.CTkLabel(amt_f, text="Amount (₹):", font=ctk.CTkFont(size=12),
                text_color="#94a3b8", anchor="w").pack(fill="x")
            self.ent_amount = ctk.CTkEntry(amt_f, placeholder_text=f"e.g. {int(rem)}",
                height=38, corner_radius=8)
            self.ent_amount.insert(0, str(int(rem)))
            self.ent_amount.pack(fill="x", pady=(4, 0))

            # Delay date (hidden by default)
            self.delay_f = ctk.CTkFrame(self, fg_color="transparent")
            ctk.CTkLabel(self.delay_f, text="New Due Date (for Delay):",
                font=ctk.CTkFont(size=12), text_color="#94a3b8", anchor="w").pack(fill="x")
            try:
                from tkcalendar import DateEntry
                self.de_delay = DateEntry(self.delay_f, date_pattern="yyyy-mm-dd",
                    background=ORANGE, foreground="white", headersbackground=NAVY,
                    normalbackground=NAVY_LIGHT, normalforeground="white",
                    font=("Segoe UI", 11), width=18, mindate=date.today())
            except ImportError:
                self.de_delay = ctk.CTkEntry(self.delay_f, placeholder_text="YYYY-MM-DD")
            self.de_delay.pack(fill="x", pady=(4, 0))
            # delay_f is NOT packed here — shown only when Delay mode selected

            # Buttons
            ctk.CTkButton(self, text="✔  Confirm Payment", height=42, corner_radius=10,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=ORANGE, hover_color=ORANGE_HOV,
                command=self._confirm,
            ).pack(fill="x", padx=20, pady=(8, 4))
            ctk.CTkButton(self, text="Cancel", height=36, corner_radius=10,
                fg_color="transparent", border_width=1, border_color="#334155",
                text_color="#94a3b8", hover_color="#1e293b",
                command=self.destroy,
            ).pack(fill="x", padx=20, pady=(0, 16))

        except Exception as e:
            import traceback
            traceback.print_exc()
            ctk.CTkLabel(self,
                text=f"⚠ Could not load dialog:\n{e}",
                text_color="#ef4444", font=ctk.CTkFont(size=12),
                wraplength=380,
            ).pack(pady=30, padx=20)
            ctk.CTkButton(self, text="Close", command=self.destroy,
                fg_color=NAVY_LIGHT).pack(pady=4)

    def _on_mode_change(self):
        mode = self.var_mode.get()
        rem  = max(0, float(self.inst["amount_due"]) - float(self.inst["amount_paid"]))
        if mode == "Full":
            self.ent_amount.delete(0, "end")
            self.ent_amount.insert(0, str(int(rem)))
            self.ent_amount.configure(state="normal")
            self.delay_f.pack_forget()
        elif mode == "Partial":
            self.ent_amount.delete(0, "end")
            self.ent_amount.configure(state="normal")
            self.delay_f.pack_forget()
        else:  # Delay
            self.ent_amount.delete(0, "end")
            self.ent_amount.configure(state="disabled")
            # Pack delay_f before the Confirm button (second-to-last child)
            children = self.winfo_children()
            if len(children) >= 2:
                self.delay_f.pack(fill="x", padx=20, pady=(0, 8),
                                  before=children[-2])
            else:
                self.delay_f.pack(fill="x", padx=20, pady=(0, 8))

    def _confirm(self):
        mode    = self.var_mode.get()
        inst_id = self.inst["inst_id"]
        today   = str(date.today())

        try:
            if mode == "Delay":
                try:
                    nd = str(self.de_delay.get_date())
                except AttributeError:
                    nd = self.de_delay.get().strip()
                self.db.mark_installment_split(inst_id, nd)
                # Also update due_date
                cursor = self.db.connection.cursor()
                cursor.execute(
                    "UPDATE installment_schedules SET due_date=%s WHERE id=%s",
                    (nd, inst_id))
                self.db.connection.commit()
                cursor.close()
            else:
                amt_str = self.ent_amount.get().strip()
                if not amt_str:
                    messagebox.showwarning("Input", "Enter an amount.", parent=self)
                    return
                amt = float(amt_str)
                if amt <= 0:
                    messagebox.showwarning("Input", "Amount must be positive.", parent=self)
                    return
                self.db.record_installment_payment(inst_id, amt, today,
                                                   payment_info=mode)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        self.destroy()
        self.on_done()


# ── Student Installments Summary Dialog ─────────────────────────────────── #

class StudentInstallmentsDialog(ctk.CTkToplevel):
    """Shows ALL installments for a student with color-coded status badges.
    Each unpaid row has a Pay button that opens PaymentDialog.
    """
    SCFG = {
        "PAID":     {"bg": "#022c22", "fg": "#6ee7b7", "badge": "#059669", "icon": "✔ PAID"},
        "PARTIAL":  {"bg": "#431407", "fg": "#fdba74", "badge": "#ea580c", "icon": "◑ PARTIAL"},
        "OVERDUE":  {"bg": "#450a0a", "fg": "#fca5a5", "badge": "#dc2626", "icon": "✖ OVERDUE"},
        "DUE SOON": {"bg": "#422006", "fg": "#fde047", "badge": "#ca8a04", "icon": "⚠ DUE SOON"},
        "UPCOMING": {"bg": "#1e1b4b", "fg": "#93c5fd", "badge": "#3b82f6", "icon": "● UPCOMING"},
    }

    def __init__(self, parent, db, student_id, student_name, on_done):
        super().__init__(parent)
        self.db           = db
        self.student_id   = student_id
        self.student_name = student_name
        self.on_done      = on_done
        self._parent      = parent

        self.title(f"Installments — {student_name}")
        self.geometry("600x520")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=NAVY)
        self._build()

    def _build(self):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(hdr, text=self.student_name,
            font=ctk.CTkFont(size=18, weight="bold"), text_color="white", anchor="w",
        ).pack(side="left")
        ctk.CTkButton(hdr, text="✕ Close", width=70, height=28, corner_radius=6,
            fg_color=NAVY_LIGHT, hover_color="#334155", text_color="#94a3b8",
            command=self.destroy,
        ).pack(side="right")

        # ── Overall summary bar ──
        student = self.db.get_student_by_id(self.student_id)
        if student:
            total_fee  = float(student.get("total_course_fee", 0))
            total_paid = float(student.get("total_paid", 0))
            balance    = float(student.get("balance", 0))
            bar = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8)
            bar.pack(fill="x", padx=20, pady=(0, 10))
            for lbl, val, clr in [
                ("Total Fee",    f"₹{total_fee:,.0f}",  "white"),
                ("Total Paid",   f"₹{total_paid:,.0f}", "#10b981"),
                ("Balance Left", f"₹{balance:,.0f}",    "#f97316"),
            ]:
                col = ctk.CTkFrame(bar, fg_color="transparent")
                col.pack(side="left", expand=True, padx=10, pady=10)
                ctk.CTkLabel(col, text=lbl, font=ctk.CTkFont(size=10),
                    text_color="#64748b").pack()
                ctk.CTkLabel(col, text=val, font=ctk.CTkFont(size=15, weight="bold"),
                    text_color=clr).pack()

        ctk.CTkFrame(self, height=1, fg_color="#334155").pack(fill="x", padx=20, pady=(0, 6))

        # ── Column labels ──
        hdr2 = ctk.CTkFrame(self, fg_color="transparent")
        hdr2.pack(fill="x", padx=24)
        for txt, w in [("Inst", 44), ("Due Date", 100), ("Due (₹)", 90),
                       ("Paid (₹)", 85), ("Remaining", 85), ("Status", 108)]:
            ctk.CTkLabel(hdr2, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b", anchor="w",
            ).pack(side="left", padx=2)

        ctk.CTkFrame(self, height=1, fg_color="#1e293b").pack(fill="x", padx=20, pady=(4, 4))

        # ── Scrollable installment rows ──
        sf = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        insts = self.db.get_installments(self.student_id)
        if not insts:
            ctk.CTkLabel(sf, text="No installments found.",
                text_color="#64748b", font=ctk.CTkFont(size=13)).pack(pady=20)
            return

        for inst in insts:
            status = inst.get("status", "UPCOMING")
            cfg    = self.SCFG.get(status, self.SCFG["UPCOMING"])

            row = ctk.CTkFrame(sf, fg_color=cfg["bg"], corner_radius=8)
            row.pack(fill="x", pady=3)

            dd = inst["due_date"]
            if isinstance(dd, str):
                from datetime import date as _d
                dd = _d.fromisoformat(dd[:10])
            due_str = dd.strftime("%d %b %Y")
            due  = float(inst["amount_due"])
            paid = float(inst["amount_paid"])
            rem  = max(0.0, due - paid)

            ctk.CTkLabel(row, text=f"#{inst['inst_no']}", width=44,
                font=ctk.CTkFont(size=13, weight="bold"), text_color=cfg["fg"], anchor="w",
            ).pack(side="left", padx=(10, 2), pady=10)
            ctk.CTkLabel(row, text=due_str, width=100,
                font=ctk.CTkFont(size=11), text_color=cfg["fg"], anchor="w",
            ).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"₹{due:,.0f}", width=90,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="white", anchor="e",
            ).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"₹{paid:,.0f}", width=85,
                font=ctk.CTkFont(size=11), text_color="#10b981", anchor="e",
            ).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"₹{rem:,.0f}", width=85,
                font=ctk.CTkFont(size=11), text_color="#f97316" if rem > 0 else "#10b981", anchor="e",
            ).pack(side="left", padx=2)

            # Status badge
            badge = ctk.CTkFrame(row, fg_color=cfg["badge"], corner_radius=5)
            badge.pack(side="left", padx=(6, 2), pady=7)
            ctk.CTkLabel(badge, text=cfg["icon"],
                font=ctk.CTkFont(size=10, weight="bold"), text_color="white",
            ).pack(padx=8, pady=3)

            # Pay button for unpaid installments
            if status != "PAID":
                inst_copy = dict(inst)
                inst_copy["_due_str"] = due_str
                inst_copy["inst_id"]  = inst["id"]
                inst_copy["name"]     = self.student_name
                inst_copy["course"]   = student["course"] if student else ""
                ctk.CTkButton(
                    row, text="💳 Pay", width=58, height=26, corner_radius=6,
                    fg_color=ORANGE, hover_color=ORANGE_HOV,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    command=lambda i=inst_copy: self._pay(i),
                ).pack(side="right", padx=8)

    def _pay(self, inst_row):
        PaymentDialog(self, self.db, inst_row, on_done=self._after_pay)

    def _after_pay(self):
        sid, sname = self.student_id, self.student_name
        self.destroy()
        StudentInstallmentsDialog(self._parent, self.db, sid, sname, self.on_done)
        self.on_done()


# ── Main View ───────────────────────────────────────────────────────────── #

class InstallmentStatusView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db        = db
        self._all_data = []
        self._build_ui()
        self.after(400, self.refresh)

    # ── UI ──────────────────────────────────────────────────────────── #

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(22, 6))

        ctk.CTkLabel(hdr, text="Installment Manager",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(hdr,
            text="View & manage every installment — due dates, payments, status at a glance",
            font=ctk.CTkFont(size=12), text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(6, 10))

        # Controls
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=30, pady=(0, 8))

        self.var_search = ctk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(ctrl, textvariable=self.var_search,
            placeholder_text="🔍  Search student name or ID…",
            height=38, corner_radius=8, width=240,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        ).pack(side="left", padx=(0, 8))

        self.var_filter = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(ctrl,
            values=["All", "OVERDUE", "PARTIAL", "DUE SOON", "UPCOMING", "PAID"],
            variable=self.var_filter, width=120, height=38, corner_radius=8,
            fg_color=("#f8fafc", NAVY), button_color=ORANGE,
            button_hover_color=ORANGE_HOV,
            command=lambda _: self._apply_filter(),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(ctrl, text="🔄  Refresh", width=105, height=38, corner_radius=8,
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(ctrl, text="💳  Pay Selected", width=120, height=38, corner_radius=8,
            fg_color="#059669", hover_color="#047857",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._pay_selected,
        ).pack(side="left")

        self.lbl_count = ctk.CTkLabel(ctrl, text="",
            font=ctk.CTkFont(size=11), text_color="#64748b")
        self.lbl_count.pack(side="right")

        # Metric cards
        self.metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_row.pack(fill="x", padx=30, pady=(0, 10))

        # Treeview card
        card = ctk.CTkFrame(self, fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=12, border_width=1,
            border_color=("#e2e8f0", "#334155"))
        card.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self._build_tree(card)

        # Hint
        ctk.CTkLabel(self,
            text="💡 Double-click a row to view all installments  |  Select row then click 💳 Pay Selected",
            font=ctk.CTkFont(size=10), text_color="#475569",
        ).pack(pady=(0, 4))

    def _build_tree(self, parent):
        tf = ctk.CTkFrame(parent, fg_color="transparent")
        tf.pack(fill="both", expand=True, padx=8, pady=8)
        tf.rowconfigure(0, weight=1)
        tf.columnconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Inst.Treeview",
            background=NAVY_LIGHT, foreground="#f8fafc",
            rowheight=40, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 11))
        style.configure("Inst.Treeview.Heading",
            background=NAVY, foreground="#cbd5e1",
            relief="flat", font=("Segoe UI", 12, "bold"), padding=(6, 8))
        style.map("Inst.Treeview",
            background=[("selected", ORANGE)],
            foreground=[("selected", "white")])

        cols = ("sid", "name", "course", "ctype",
                "inst_no", "due_date", "amount_due",
                "amount_paid", "remaining", "paid_on", "status")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings",
                                  style="Inst.Treeview", selectmode="browse")

        headers = [
            ("sid",        "ID",         55,  "center"),
            ("name",       "Student",    150, "w"),
            ("course",     "Course",     85,  "w"),
            ("ctype",      "Type",       85,  "w"),
            ("inst_no",    "Inst #",     52,  "center"),
            ("due_date",   "Due Date",   95,  "center"),
            ("amount_due", "Due (₹)",    90,  "e"),
            ("amount_paid","Paid (₹)",   90,  "e"),
            ("remaining",  "Remaining",  90,  "e"),
            ("paid_on",    "Paid On",    95,  "center"),
            ("status",     "Status",     90,  "center"),
        ]
        for col, text, width, anchor in headers:
            self.tree.heading(col, text=text, anchor=anchor,
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=width, anchor=anchor, minwidth=40)

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("PAID",     background="#022c22", foreground="#6ee7b7")
        self.tree.tag_configure("PARTIAL",  background="#431407", foreground="#fdba74")
        self.tree.tag_configure("OVERDUE",  background="#3b0a0a", foreground="#fca5a5")
        self.tree.tag_configure("DUE SOON", background="#422006", foreground="#fde047")
        self.tree.tag_configure("UPCOMING", background="#1e1b4b", foreground="#93c5fd")

        self.tree.bind("<Double-1>", self._on_double_click)
        self._sort_col = None
        self._sort_rev = False

    # ── Data ────────────────────────────────────────────────────────── #

    def refresh(self):
        self.lbl_count.configure(text="⏳ Loading…")
        # Run synchronously to avoid shared DB connection crash
        try:
            today = date.today()
            cursor = self.db.connection.cursor(dictionary=True)

            # Fetch installments + student info + latest payment date
            cursor.execute("""
                SELECT
                    i.id          AS inst_id,
                    i.student_id,
                    i.inst_no,
                    i.due_date,
                    i.amount_due,
                    i.amount_paid,
                    i.split_due_date,
                    s.name,
                    s.course,
                    s.course_type
                FROM installment_schedules i
                JOIN students s ON i.student_id = s.id
                ORDER BY s.id, i.inst_no
            """)
            rows = cursor.fetchall()
            cursor.close()

            from itertools import groupby
            rows.sort(key=lambda x: (x["student_id"], x["inst_no"]))

            result = []
            for sid, group in groupby(rows, key=lambda x: x["student_id"]):
                has_past_due = False
                insts_with_status = []
                for r in group:
                    paid = float(r["amount_paid"])
                    due  = float(r["amount_due"])
                    dd   = r["due_date"]
                    if isinstance(dd, str):
                        dd = date.fromisoformat(dd[:10])

                    if paid >= due - 0.01:
                        status = "PAID"
                    else:
                        if has_past_due:
                            status = "OVERDUE"
                        elif paid > 0:
                            if dd < today:
                                status = "OVERDUE"
                                has_past_due = True
                            else:
                                status = "PARTIAL"
                        elif dd < today:
                            status = "OVERDUE"
                            has_past_due = True
                        elif dd <= today + timedelta(days=3):
                            status = "DUE SOON"
                        else:
                            status = "UPCOMING"

                    # paid_on: use split_due_date as a proxy if delayed, else blank for unpaid
                    paid_on = ""
                    if status == "PAID":
                        # Use split_due_date if set (means it was delayed then paid)
                        if r.get("split_due_date"):
                            paid_on = str(r["split_due_date"])
                        else:
                            paid_on = "—"

                    insts_with_status.append({
                        **r,
                        "_status":    status,
                        "_due":       dd,
                        "_due_str":   dd.strftime("%d %b %Y"),
                        "_remaining": max(0.0, due - paid),
                        "_paid_on":   paid_on,
                    })

                # Pick the most relevant installment for this student:
                # First unpaid installment, or the last paid installment if all are paid
                if insts_with_status:
                    active_inst = next((i for i in insts_with_status if i["_status"] != "PAID"), None)
                    if active_inst:
                        result.append(active_inst)
                    else:
                        result.append(insts_with_status[-1])

            self._render(result)
        except Exception as e:
            self.lbl_count.configure(text=f"⚠ Error: {e}", text_color="#dc2626")

    def _render(self, data):
        self._all_data = data
        self._apply_filter()
        self._update_metrics(data)

    def _apply_filter(self):
        q    = self.var_search.get().strip().lower()
        filt = self.var_filter.get()
        data = self._all_data

        if q:
            data = [r for r in data if
                    q in r["name"].lower() or q in str(r["student_id"])]
        if filt != "All":
            data = [r for r in data if r["_status"] == filt]

        self._fill_tree(data)
        students = len({r["student_id"] for r in data})
        self.lbl_count.configure(
            text=f"Showing {students} active student records",
            text_color="#64748b")

    def _fill_tree(self, data):
        self.tree.delete(*self.tree.get_children())
        for r in data:
            st    = r["_status"]
            label = STATUS_CFG[st]["label"]
            self.tree.insert("", "end", iid=r["inst_id"], values=(
                f"#{r['student_id']:03d}",
                r["name"],
                r["course"],
                r.get("course_type", "Annual"),
                f"#{r['inst_no']}",
                r["_due_str"],
                f"₹{float(r['amount_due']):,.0f}",
                f"₹{float(r['amount_paid']):,.0f}",
                f"₹{r['_remaining']:,.0f}",
                r["_paid_on"] or "—",
                label,
            ), tags=(st,))

    def _update_metrics(self, data):
        for w in self.metrics_row.winfo_children():
            w.destroy()

        counts  = {k: 0   for k in STATUS_CFG}
        amounts = {k: 0.0 for k in STATUS_CFG}
        for r in data:
            st = r["_status"]
            counts[st]  += 1
            amounts[st] += r["_remaining"]

        display = [
            ("🔴 Overdue",  "OVERDUE",  f"₹{amounts['OVERDUE']:,.0f}"),
            ("🟡 Due Soon", "DUE SOON", f"₹{amounts['DUE SOON']:,.0f}"),
            ("🔵 Upcoming", "UPCOMING", f"₹{amounts['UPCOMING']:,.0f}"),
            ("🟢 Paid",     "PAID",     f"{counts['PAID']} cleared"),
        ]
        for title, key, sub in display:
            color = STATUS_CFG[key]["color"]
            card  = ctk.CTkFrame(self.metrics_row,
                fg_color=("#ffffff", NAVY_LIGHT), corner_radius=10,
                border_width=2, border_color=color)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))
            ctk.CTkLabel(card, text=title,
                font=ctk.CTkFont(size=11), text_color="#64748b",
            ).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(card, text=str(counts[key]),
                font=ctk.CTkFont(size=22, weight="bold"), text_color=color,
            ).pack(anchor="w", padx=14)
            ctk.CTkLabel(card, text=sub,
                font=ctk.CTkFont(size=11), text_color="#64748b",
            ).pack(anchor="w", padx=14, pady=(0, 10))

    # ── Actions ─────────────────────────────────────────────────────── #

    def _pay_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select Row",
                "Please click a row first, then press Pay.", parent=self)
            return
        inst_id = int(sel[0])
        # Find the row data
        row = next((r for r in self._all_data if r["inst_id"] == inst_id), None)
        if not row:
            return
        if row["_status"] == "PAID":
            messagebox.showinfo("Already Paid",
                f"Installment #{row['inst_no']} is already fully paid.", parent=self)
            return
        PaymentDialog(self, self.db, row, on_done=self.refresh)

    def _on_double_click(self, event):
        """Open full installment summary for the clicked student."""
        sel = self.tree.selection()
        if not sel:
            return
        inst_id = int(sel[0])
        row = next((r for r in self._all_data if r["inst_id"] == inst_id), None)
        if not row:
            return
        StudentInstallmentsDialog(
            self, self.db,
            student_id=row["student_id"],
            student_name=row["name"],
            on_done=self.refresh,
        )

    def _sort_by(self, col):
        """Click column header to sort."""
        data = list(self._all_data)
        col_map = {
            "sid":        lambda r: r["student_id"],
            "name":       lambda r: r["name"].lower(),
            "course":     lambda r: r["course"].lower(),
            "ctype":      lambda r: r.get("course_type", ""),
            "inst_no":    lambda r: r["inst_no"],
            "due_date":   lambda r: r["_due"],
            "amount_due": lambda r: float(r["amount_due"]),
            "amount_paid":lambda r: float(r["amount_paid"]),
            "remaining":  lambda r: r["_remaining"],
            "status":     lambda r: r["_status"],
        }
        if col not in col_map:
            return
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        data.sort(key=col_map[col], reverse=self._sort_rev)
        self._all_data = data
        self._apply_filter()
