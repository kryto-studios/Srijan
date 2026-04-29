"""
views/installment_manager.py
-----------------------------
Installment Manager — view & edit every student's installment schedule.
Clean all-pack() layout that works standalone AND embedded inside tabs.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"

DISCOUNT_DEFAULTS = {1: 3.0, 2: 2.0}


class InstallmentManagerView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._selected_student = None
        self._inst_rows = []
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────── #

    def _build_ui(self):
        # Two-column body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=6)

        # Left 30%
        left = ctk.CTkFrame(body, fg_color=(("#ffffff", NAVY_LIGHT)),
            corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"),
            width=260)
        left.pack(side="left", fill="y", padx=(0, 8), pady=4)
        left.pack_propagate(False)
        self._build_left(left)

        # Right 70%
        right_wrap = ctk.CTkFrame(body, fg_color="transparent")
        right_wrap.pack(side="left", fill="both", expand=True, pady=4)
        self.right = ctk.CTkScrollableFrame(right_wrap,
            fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        self.right.pack(fill="both", expand=True)
        self._build_right()

    def _build_left(self, parent):
        # Search
        sf = ctk.CTkFrame(parent, fg_color="transparent")
        sf.pack(fill="x", padx=10, pady=(10, 6))
        self.var_search = ctk.StringVar()
        self.var_search.trace_add("write", lambda *_: self._load_students())
        ctk.CTkEntry(sf, textvariable=self.var_search,
            placeholder_text="Search student…", height=36, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#3f3f46"),
        ).pack(fill="x")

        # Treeview
        tf = ctk.CTkFrame(parent, fg_color="transparent")
        tf.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("IM.Treeview",
            background=NAVY_LIGHT, foreground="#e2e8f0",
            rowheight=36, fieldbackground=NAVY_LIGHT,
            borderwidth=0, font=("Segoe UI", 10))
        style.configure("IM.Treeview.Heading",
            background=NAVY, foreground="#94a3b8",
            relief="flat", font=("Segoe UI", 10, "bold"), padding=(4, 6))
        style.map("IM.Treeview",
            background=[("selected", ORANGE)], foreground=[("selected", "white")])

        cols = ("id", "name", "insts")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", style="IM.Treeview")
        self.tree.heading("id",    text="ID",   anchor="center")
        self.tree.heading("name",  text="Name", anchor="w")
        self.tree.heading("insts", text="#",    anchor="center")
        self.tree.column("id",    width=48,  anchor="center", stretch=False)
        self.tree.column("name",  width=140, anchor="w",      stretch=True)
        self.tree.column("insts", width=38,  anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_right(self):
        # Student name / placeholder
        self.lbl_title = ctk.CTkLabel(self.right,
            text="← Select a student",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w")
        self.lbl_title.pack(fill="x", padx=14, pady=(12, 2))

        self.lbl_sub = ctk.CTkLabel(self.right, text="",
            font=ctk.CTkFont(size=11), text_color="#64748b", anchor="w")
        self.lbl_sub.pack(fill="x", padx=14, pady=(0, 8))

        # Discount row
        disc_f = ctk.CTkFrame(self.right,
            fg_color=("#f0fdf4", "#052e16"), corner_radius=8,
            border_width=1, border_color=("#86efac", "#166534"))
        disc_f.pack(fill="x", padx=14, pady=(0, 8))
        di = ctk.CTkFrame(disc_f, fg_color="transparent")
        di.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(di, text="🎉 Discount (%)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#065f46", "#34d399")).pack(side="left")
        self.ent_discount = ctk.CTkEntry(di, width=70, height=32, corner_radius=6,
            border_width=1, border_color=("#86efac", "#166534"))
        self.ent_discount.insert(0, "0")
        self.ent_discount.pack(side="left", padx=8)
        self.ent_discount.bind("<KeyRelease>", lambda _: self._update_totals())
        self.lbl_disc_info = ctk.CTkLabel(di, text="",
            font=ctk.CTkFont(size=11), text_color=("#059669", "#34d399"))
        self.lbl_disc_info.pack(side="left")

        # Section label
        ctk.CTkLabel(self.right, text="📅  Installment Schedule",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w").pack(fill="x", padx=14, pady=(0, 2))
        ctk.CTkFrame(self.right, height=1,
            fg_color=("#e2e8f0", "#27272a")).pack(fill="x", padx=14, pady=(0, 6))

        # Column header row (using same pack widths as data rows)
        hdr = ctk.CTkFrame(self.right, fg_color=("#f1f5f9", NAVY), corner_radius=6)
        hdr.pack(fill="x", padx=14, pady=(0, 3))
        for txt, w in [("#", 42), ("Due Date (YYYY-MM-DD)", 148), ("Amount (₹)", 100),
                        ("Status / Action", 0)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=("#64748b", "#94a3b8"), anchor="w",
            ).pack(side="left", padx=6, pady=5)

        # Installment rows container
        self.rows_frame = ctk.CTkFrame(self.right, fg_color="transparent")
        self.rows_frame.pack(fill="x", padx=14)

        # Totals card
        tot_f = ctk.CTkFrame(self.right,
            fg_color=("#f0fdf4", "#052e16"), corner_radius=8,
            border_width=1, border_color=("#86efac", "#166534"))
        tot_f.pack(fill="x", padx=14, pady=(8, 0))
        ti = ctk.CTkFrame(tot_f, fg_color="transparent")
        ti.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(ti, text="Total of installments:",
            font=ctk.CTkFont(size=12), text_color="#64748b").pack(side="left")
        self.lbl_sum = ctk.CTkLabel(ti, text="₹0",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#059669")
        self.lbl_sum.pack(side="left", padx=8)
        self.lbl_match = ctk.CTkLabel(ti, text="",
            font=ctk.CTkFont(size=11))
        self.lbl_match.pack(side="left")

        # Save button
        ctk.CTkButton(self.right, text="💾  Save Changes", height=42, corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._save_changes,
        ).pack(fill="x", padx=14, pady=(10, 4))

        self.lbl_save_status = ctk.CTkLabel(self.right, text="",
            font=ctk.CTkFont(size=12), anchor="w")
        self.lbl_save_status.pack(fill="x", padx=14, pady=(0, 12))

    # ── Data ──────────────────────────────────────────────────────── #

    def refresh(self):
        self._load_students()

    def _load_students(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            q = self.var_search.get()
            students = self.db.search_students(q)
            # Single query for all installment counts — no N+1
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT student_id, COUNT(*) AS n "
                "FROM installment_schedules GROUP BY student_id"
            )
            counts = {r["student_id"]: r["n"] for r in cursor.fetchall()}
            cursor.close()
            for s in students:
                n = counts.get(s["id"], 0)
                self.tree.insert("", "end", iid=s["id"], values=(
                    f"#{s['id']:03d}", s["name"], n or "-"
                ))
        except Exception as e:
            print(f"[IM] load error: {e}")


    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        sid = int(sel[0])
        try:
            s     = self.db.get_student_by_id(sid)
            insts = self.db.get_installments(sid)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._selected_student = s
        freq = s.get("fee_frequency", "2")
        n    = int(freq) if str(freq).isdigit() else 1
        disc = DISCOUNT_DEFAULTS.get(n, 0.0)

        self.lbl_title.configure(text=f"📋  {s['name']}")
        self.lbl_sub.configure(
            text=f"#{s['id']:03d}  ·  {s['course']}  ·  "
                 f"Fee ₹{float(s['total_course_fee']):,.2f}  ·  {n} installment{'s' if n>1 else ''}")
        self.ent_discount.delete(0, "end")
        self.ent_discount.insert(0, f"{disc:.1f}")
        self.lbl_save_status.configure(text="")
        self._render_inst_rows(insts)

    def _render_inst_rows(self, insts):
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self._inst_rows = []

        if not insts:
            ctk.CTkLabel(self.rows_frame,
                text="No installment schedule yet. Register a student to auto-create one.",
                font=ctk.CTkFont(size=12), text_color="#64748b",
            ).pack(pady=12)
            return

        ST = {
            "PAID":    "#10b981",
            "PARTIAL": "#f59e0b",
            "UPCOMING": "#3b82f6",
            "PENDING": "#3b82f6",
            "OVERDUE": "#ef4444",
            "DUE SOON": "#f97316",
        }
        BG = {
            "PAID":    ("#f0fdf4", "#052e16"),
            "PARTIAL": ("#fffbeb", "#451a03"),
            "UPCOMING": ("#eff6ff", "#1e1b4b"),
            "PENDING": ("#ffffff", "#0f172a"),
            "OVERDUE": ("#fef2f2", "#450a0a"),
            "DUE SOON": ("#fffbeb", "#7c2d12"),
        }

        # ── Header Row ──
        header = ctk.CTkFrame(self.rows_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header, text="Inst #", width=50, anchor="w", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(8, 6))
        ctk.CTkLabel(header, text="Due Date (YYYY-MM-DD)", width=170, anchor="w", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(header, text="Amount (₹)", width=100, anchor="w", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(header, text="Status / Action", width=110, anchor="w", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 8))

        for inst in insts:
            dd      = inst["due_date"]
            due_str = dd.strftime("%Y-%m-%d") if hasattr(dd, "strftime") else str(dd)
            status  = inst["status"]
            color   = ST.get(status, "#3b82f6")
            is_paid = (status == "PAID")
            
            # Map DB status to UI choice
            if status in ["UPCOMING", "DUE SOON", "OVERDUE", "PENDING"]:
                ui_choice = "Pay Later"
            elif status == "PARTIAL":
                ui_choice = "Partial"
            elif status == "PAID":
                ui_choice = "Pay Now"
            else:
                ui_choice = "Pay Later"

            row = ctk.CTkFrame(self.rows_frame,
                fg_color=BG.get(status, BG["PENDING"]),
                corner_radius=8, border_width=1, border_color=color)
            row.pack(fill="x", pady=3)

            # ── #N badge ──
            badge_f = ctk.CTkFrame(row,
                fg_color="#059669" if is_paid else color,
                corner_radius=6, width=42, height=28)
            badge_f.pack_propagate(False)
            badge_f.pack(side="left", padx=(8, 6), pady=8)
            ctk.CTkLabel(badge_f, text=f"#{inst['inst_no']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white").pack(expand=True)

            # ── Due date entry ──
            from tkcalendar import DateEntry
            date_f = ctk.CTkFrame(row, fg_color="transparent")
            date_f.pack(side="left", padx=(0, 6))
            ent_date = DateEntry(date_f, width=15, background='#0f172a',
                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
            ent_date.set_date(due_str)
            ent_date.pack(side="left", fill="both", expand=True)

            # ── Price entry ──
            ent_due = ctk.CTkEntry(row, width=85, height=32, corner_radius=6,
                border_width=1, border_color=("#e2e8f0", "#334155"))
            ent_due.insert(0, f"{float(inst['amount_due']):.2f}")
            ent_due.pack(side="left", padx=(0, 6))
            ent_due.bind("<KeyRelease>", lambda _: self._update_totals())

            # ── Status Badge ──
            status_f = ctk.CTkFrame(row, fg_color=color, corner_radius=6, width=80, height=32)
            status_f.pack_propagate(False)
            status_f.pack(side="left", padx=(8, 10))
            ctk.CTkLabel(status_f, text=status,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white").pack(expand=True)

            # ── Action Button (Popup) ──
            if not is_paid:
                btn_pay = ctk.CTkButton(row, text="💳 Pay", width=70, height=32, corner_radius=6,
                    font=ctk.CTkFont(weight="bold", size=12),
                    fg_color="#059669", hover_color="#047857",
                    command=lambda i=inst: self._open_payment_dialog(i))
                btn_pay.pack(side="left")
            else:
                ctk.CTkLabel(row, text="✔ Completed", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#059669").pack(side="left", padx=10)

            # paid info line under row (for PARTIAL)
            if status == "PARTIAL":
                paid_lbl = ctk.CTkLabel(self.rows_frame,
                    text=f"     ↳ Paid ₹{float(inst['amount_paid']):,.2f} of ₹{float(inst['amount_due']):,.2f}  "
                         f"(₹{float(inst['amount_due']) - float(inst['amount_paid']):,.2f} remaining)",
                    font=ctk.CTkFont(size=10), text_color="#f59e0b", anchor="w")
                paid_lbl.pack(fill="x", pady=(0, 2))

            self._inst_rows.append({
                "id":       inst["id"],
                "ent_date": ent_date,
                "ent_due":  ent_due,
                "inst_no":  inst["inst_no"],
                "student_id": inst["student_id"],
                "status": status,
                "paid": float(inst["amount_paid"])
            })

        self._update_totals()

    def _open_payment_dialog(self, inst):
        """Open the PaymentDialog popup for this installment."""
        PaymentDialog(self, self.db, inst, self._selected_student, self._on_payment_success)

    def _on_payment_success(self, inst_no):
        """Callback after a successful payment via the dialog."""
        self._load_students()
        sid = self._selected_student["id"]
        try:
            self._selected_student = self.db.get_student_by_id(sid)
            insts = self.db.get_installments(sid)
            self._render_inst_rows(insts)
            try:
                self.tree.selection_set(str(sid))
            except Exception:
                pass
            self.lbl_save_status.configure(
                text=f"✅  Payment recorded for Installment #{inst_no}!",
                text_color="#059669")
        except Exception as e:
            self.lbl_save_status.configure(
                text=f"✖  Refresh error: {e}", text_color="#dc2626")

    # ── Totals ────────────────────────────────────────────────────── #

    def _update_totals(self):
        if not self._selected_student:
            return
        total_fee = float(self._selected_student["total_course_fee"])
        try:
            disc_pct = float(self.ent_discount.get().strip() or 0)
        except ValueError:
            disc_pct = 0
        effective = total_fee * (1 - disc_pct / 100)
        saved = total_fee - effective
        self.lbl_disc_info.configure(
            text=f"  Save ₹{saved:,.2f}  →  Payable ₹{effective:,.2f}" if disc_pct > 0 else "  No discount")

        total_inst = 0.0
        for r in self._inst_rows:
            if r["status"] == "PAID":
                total_inst += r["paid"]
                continue
            try:
                total_inst += float(r["ent_due"].get().strip() or 0)
            except ValueError:
                pass
        self.lbl_sum.configure(text=f"₹{total_inst:,.2f}")

        diff = abs(total_inst - effective)
        if diff < 1:
            self.lbl_match.configure(text="✅ Matches", text_color="#059669")
        else:
            self.lbl_match.configure(
                text=f"⚠ ₹{diff:,.2f} diff", text_color="#dc2626")

    # ── Save ──────────────────────────────────────────────────────── #

    def _save_changes(self):
        if not self._selected_student:
            self.lbl_save_status.configure(
                text="⚠ Select a student first.", text_color="#dc2626")
            return
        if not self._inst_rows:
            self.lbl_save_status.configure(
                text="⚠ No installments to save.", text_color="#dc2626")
            return
        try:
            saved = 0
            for r in self._inst_rows:
                new_date = r["ent_date"].get().strip()
                new_due  = float(r["ent_due"].get().strip() or 0)
                
                if not new_date:
                    raise ValueError("Date cannot be empty.")
                
                # Update just the due date and amount
                self.db.update_installment(r["id"], new_date, new_due)
                saved += 1

            self.lbl_save_status.configure(
                text=f"✔  {saved} installment{'s' if saved != 1 else ''} saved!",
                text_color="#059669")
            self._load_students()
            try:
                self.tree.selection_set(str(self._selected_student["id"]))
                self._on_select()
            except Exception:
                pass
        except Exception as e:
            self.lbl_save_status.configure(text=f"✖  {e}", text_color="#dc2626")


class PaymentDialog(ctk.CTkToplevel):
    """A popup dialog to record full, partial, or delayed payments."""
    def __init__(self, parent, db, inst, student, success_callback):
        super().__init__(parent)
        self.db = db
        self.inst = inst
        self.student = student
        self.success_callback = success_callback
        
        self.title("Record Payment")
        self.geometry("420x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Calculate remaining
        self.amt_due = float(inst['amount_due'])
        self.amt_paid = float(inst['amount_paid'])
        self.remaining = self.amt_due - self.amt_paid

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=("#f8fafc", "#0f172a"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"Installment #{self.inst['inst_no']} Payment",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=20, weight="bold"),
            text_color="#c2410c").pack(pady=(16, 4))
        ctk.CTkLabel(hdr, text=f"{self.student['name']}  ·  Remaining: ₹{self.remaining:,.2f}",
            font=ctk.CTkFont(size=12), text_color="#64748b").pack(pady=(0, 16))

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # Method
        ctk.CTkLabel(body, text="Payment Method:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.var_method = ctk.StringVar(value="Pay Full Amount Now")
        om = ctk.CTkOptionMenu(body, variable=self.var_method,
            values=["Pay Full Amount Now", "Pay Partial Amount", "Delay to Later Date"],
            command=self._on_method_change, width=370, height=36)
        om.pack(anchor="w", pady=(4, 16))

        # (payment_info is set automatically as "Installment #N")

        # Amount Frame
        self.f_amount = ctk.CTkFrame(body, fg_color="transparent")
        self.f_amount.pack(fill="x", pady=4)
        ctk.CTkLabel(self.f_amount, text="Amount Paying Today (₹):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.ent_amount = ctk.CTkEntry(self.f_amount, width=370, height=36)
        self.ent_amount.insert(0, f"{self.remaining:.2f}")
        self.ent_amount.pack(anchor="w", pady=(4, 0))

        # Date Frame
        self.f_date = ctk.CTkFrame(body, fg_color="transparent")
        self.f_date.pack(fill="x", pady=12)
        ctk.CTkLabel(self.f_date, text="Follow-up Date (YYYY-MM-DD):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        from tkcalendar import DateEntry
        self.date_picker = DateEntry(self.f_date, width=15, background='#0f172a',
                                     foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_picker.pack(anchor="w", pady=(4, 0))
        
        # Initial UI state
        self._on_method_change(self.var_method.get())

        # Error label
        self.lbl_err = ctk.CTkLabel(body, text="", text_color="#dc2626", font=ctk.CTkFont(size=11))
        self.lbl_err.pack(pady=4)

        # Buttons
        btn_f = ctk.CTkFrame(body, fg_color="transparent")
        btn_f.pack(fill="x", side="bottom", pady=8)
        
        ctk.CTkButton(btn_f, text="Cancel", width=100, fg_color="#64748b", hover_color="#475569",
            command=self.destroy).pack(side="left")
        ctk.CTkButton(btn_f, text="Confirm Payment", width=140, fg_color="#059669", hover_color="#047857",
            font=ctk.CTkFont(weight="bold"), command=self._confirm).pack(side="right")

    def _on_method_change(self, method):
        if method == "Pay Full Amount Now":
            self.ent_amount.configure(state="normal")
            self.ent_amount.delete(0, "end")
            self.ent_amount.insert(0, f"{self.remaining:.2f}")
            self.ent_amount.configure(state="disabled")
            self.date_picker.configure(state="disabled")
        elif method == "Pay Partial Amount":
            self.ent_amount.configure(state="normal")
            self.ent_amount.delete(0, "end")
            self.ent_amount.insert(0, "")
            self.date_picker.configure(state="normal")
        else: # Delay to Later Date
            self.ent_amount.configure(state="normal")
            self.ent_amount.delete(0, "end")
            self.ent_amount.insert(0, "0.00")
            self.ent_amount.configure(state="disabled")
            self.date_picker.configure(state="normal")

    def _confirm(self):
        method = self.var_method.get()
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")

        try:
            amt = float(self.ent_amount.get().strip() or 0)
        except ValueError:
            self.lbl_err.configure(text="Invalid amount entered.")
            return

        if amt > self.remaining + 0.01:
            self.lbl_err.configure(text="Cannot pay more than remaining balance.")
            return

        split_date = None
        if method in ("Pay Partial Amount", "Delay to Later Date"):
            split_date = self.date_picker.get()
            if not split_date:
                self.lbl_err.configure(text="Follow-up date is required.")
                return

        try:
            if method == "Delay to Later Date":
                # Only updating split date
                self.db.mark_installment_split(self.inst["id"], split_date)
            else:
                # Record payment (full or partial)
                self.db.record_installment_payment(
                    inst_id=self.inst["id"],
                    amount=amt,
                    payment_date=today_str,
                    split_due_date=split_date,
                    payment_info=f"Installment #{self.inst['inst_no']}"
                )
            self.success_callback(self.inst["inst_no"])
            self.destroy()
        except Exception as e:
            self.lbl_err.configure(text=f"Database error: {e}")
