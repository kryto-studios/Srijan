"""
views/add_student.py
--------------------
Student registration form + inline installment manager — Srijan Institute.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
from utils.fee_calculator import INSTALLMENT_OPTIONS
from tkcalendar import DateEntry
from views.installment_manager import InstallmentManagerView

# ── Institute Palette ──────────────────────────────────────────────────────
ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class AddStudentView(ctk.CTkFrame):
    COURSES = [
        "NEET", "JEE",
        "6th", "7th", "8th", "9th", "10th", "11th", "12th",
    ]
    
    COURSE_SUBJECTS = {
        "NEET": ["Physics", "Chemistry", "Biology", "English", "Mock Tests"],
        "JEE": ["Physics", "Chemistry", "Mathematics", "English", "Mock Tests"],
        "11th": ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science", "English", "Hindi"],
        "12th": ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science", "English", "Hindi"],
        "10th": ["Mathematics", "Science", "Social Science", "English", "Hindi"],
        "9th": ["Mathematics", "Science", "Social Science", "English", "Hindi"],
        "8th": ["Mathematics", "Science", "Social Science", "English"],
        "7th": ["Mathematics", "Science", "Social Science", "English"],
        "6th": ["Mathematics", "Science", "Social Science", "English"],
    }

    COURSE_TYPES = ["Annual Course", "Summer Course", "Crash Course", "Test Series"]
    COURSE_TYPE_MONTHS = {"Annual Course": 12, "Summer Course": 2, "Crash Course": 1, "Test Series": 3}
    GENDERS     = ["Male", "Female", "Other", "Not Specified"]
    CATEGORIES  = ["General", "OBC", "SC", "ST"]

    def __init__(self, parent, db, on_success=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db         = db
        self.on_success = on_success
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────── #

    def _build_ui(self):
        # ── Page Header ──────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(22, 8))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(title_f, text="Admission & Installments",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=26, weight="bold"),
        ).pack(anchor="w")
        self.lbl_sub = ctk.CTkLabel(title_f,
            text="Enroll a new student or manage existing installment schedules",
            font=ctk.CTkFont(size=12), text_color="#64748b")
        self.lbl_sub.pack(anchor="w")

        # ── Tab Bar ──────────────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(self, fg_color=("#f1f5f9", NAVY_LIGHT), corner_radius=12)
        tab_bar.pack(fill="x", padx=30, pady=(4, 0))
        tab_inner = ctk.CTkFrame(tab_bar, fg_color="transparent")
        tab_inner.pack(padx=6, pady=6, anchor="w")

        self._tab_btns = {}
        for tab_id, label in [("admission", "📝  New Admission"),
                              ("installments", "📊  Manage Installments")]:
            btn = ctk.CTkButton(
                tab_inner, text=label, width=190, height=36, corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent", text_color="#64748b",
                hover_color=("#e2e8f0", "#334155"),
                command=lambda t=tab_id: self._switch_tab(t),
            )
            btn.pack(side="left", padx=(0, 4))
            self._tab_btns[tab_id] = btn

        ctk.CTkFrame(self, height=1, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(6, 0))

        # ── Tab Content Frames ────────────────────────────────────────────
        self.frame_admission    = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_installments = InstallmentManagerView(self, self.db)

        self.frame_admission.pack(fill="both", expand=True)
        self._current_tab = "admission"
        self._build_admission_form(self.frame_admission)
        self._switch_tab("admission")

    def _switch_tab(self, tab_id: str):
        self._current_tab = tab_id
        ACTIVE   = {"fg_color": ORANGE,      "text_color": "white",   "hover_color": ORANGE_HOV}
        INACTIVE = {"fg_color": "transparent","text_color": "#64748b", "hover_color": ("#e2e8f0", "#334155")}
        for tid, btn in self._tab_btns.items():
            btn.configure(**(ACTIVE if tid == tab_id else INACTIVE))

        if tab_id == "admission":
            self.frame_installments.pack_forget()
            self.frame_admission.pack(fill="both", expand=True)
            self.lbl_sub.configure(text="Enroll a new student below")
        else:
            self.frame_admission.pack_forget()
            self.frame_installments.pack(fill="both", expand=True)
            self.frame_installments.refresh()
            self.lbl_sub.configure(text="View & manage student installment schedules")

    def _build_admission_form(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30)

        card = ctk.CTkFrame(
            scroll, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=16,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        card.pack(fill="x", pady=5)
        inn = ctk.CTkFrame(card, fg_color="transparent")
        inn.pack(fill="both", expand=True, padx=30, pady=25)

        # ── Personal Info ────────────────────────────────────────────────
        self._section(inn, "\uE77B  Personal Information")
        r1 = self._row(inn)
        self.ent_name        = self._entry(r1, 0, "Student Full Name *", "e.g. Aarav Sharma")
        self.ent_father_name = self._entry(r1, 1, "Father's Name *",     "e.g. Rajesh Sharma")

        r2 = self._row(inn)
        self.de_dob    = self._date_picker(r2, 0, "Date of Birth *")
        self.ent_phone = self._entry(r2, 1, "Student Phone", "e.g. 9876543210")

        r2p = self._row(inn)
        self.ent_parent_phone = self._entry(r2p, 0, "Parent Phone Number", "e.g. 9876543210")

        r2b = self._row(inn)
        self.var_gender   = ctk.StringVar(value=self.GENDERS[0])
        self.var_category = ctk.StringVar(value=self.CATEGORIES[0])
        self._dropdown(r2b, 0, "Gender", self.GENDERS, self.var_gender)
        self._dropdown(r2b, 1, "Category", self.CATEGORIES, self.var_category)

        r2c = self._row(inn)
        self.var_course = ctk.StringVar(value=self.COURSES[0])
        self._dropdown(r2c, 0, "Course / Class *", self.COURSES, self.var_course)
        
        # ── Subjects Panel ──
        self.subj_frame = ctk.CTkFrame(inn, fg_color="transparent")
        self.subj_frame.pack(fill="x", pady=(10, 0))
        self.subj_vars = {} # Dictionary to store Checkbox variables
        
        # Monitor course changes to update subjects
        self.var_course.trace_add("write", self._update_subjects_ui)
        self._update_subjects_ui() # Trigger initial render

        # ── Address ──────────────────────────────────────────────────────
        self._section(inn, "\uE819  Address")
        ctk.CTkLabel(
            inn, text="Address *",
            font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8"), anchor="w",
        ).pack(fill="x")
        self.txt_address = ctk.CTkTextbox(
            inn, height=72, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        self.txt_address.pack(fill="x", pady=(4, 0))

        # ── Fee Structure ────────────────────────────────────────────────
        self._section(inn, "\uE825  Fee Structure")
        r3 = self._row(inn)
        self.ent_fee       = self._entry(r3, 0, "Total Course Fee (₹) *", "e.g. 45000")
        self.var_ctype     = ctk.StringVar(value=self.COURSE_TYPES[0])
        self._dropdown(r3, 1, "Course Type *", self.COURSE_TYPES, self.var_ctype)

        r4 = self._row(inn)
        self.var_freq = ctk.StringVar(value="2")
        self._dropdown(r4, 0, "No. of Installments *", INSTALLMENT_OPTIONS, self.var_freq)
        self.de_admission = self._date_picker(r4, 1, "Admission Date *")
        self.var_ctype.trace_add("write", self._update_preview)

        # ── Discount Row ──────────────────────────────────────────────────
        disc_row = ctk.CTkFrame(inn, fg_color=("#f0fdf4", "#052e16"),
            corner_radius=8, border_width=1, border_color=("#86efac", "#166534"))
        disc_row.pack(fill="x", pady=(8, 0))
        disc_inner = ctk.CTkFrame(disc_row, fg_color="transparent")
        disc_inner.pack(fill="x", padx=14, pady=8)
        disc_inner.columnconfigure(1, weight=1)

        ctk.CTkLabel(disc_inner, text="🎉  Discount (%)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=("#065f46", "#34d399"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.ent_discount = ctk.CTkEntry(disc_inner, width=80, height=34, corner_radius=8,
            border_width=1, border_color=("#86efac", "#166534"),
            placeholder_text="0",
        )
        self.ent_discount.insert(0, "0")
        self.ent_discount.grid(row=0, column=1, sticky="w")
        self.lbl_disc_info = ctk.CTkLabel(disc_inner, text="",
            font=ctk.CTkFont(size=11), text_color=("#059669", "#34d399"))
        self.lbl_disc_info.grid(row=0, column=2, sticky="e", padx=(10, 0))
        ctk.CTkLabel(disc_inner,
            text="  ← 1 installment = 3% auto | 2 installments = 2% auto | 3+ = customize",
            font=ctk.CTkFont(size=10), text_color=("#64748b", "#6b7280"),
        ).grid(row=1, column=0, columnspan=3, sticky="w")

        # ── Fee Preview ──────────────────────────────────────────────────
        prev_frame = ctk.CTkFrame(
            inn, fg_color=("#fff7ed", "#431407"),
            corner_radius=8, border_width=1, border_color=("#fed7aa", "#7c2d12"),
        )
        prev_frame.pack(fill="x", pady=(12, 0))
        self.preview_inner = ctk.CTkFrame(prev_frame, fg_color="transparent")
        self.preview_inner.pack(fill="x", padx=14, pady=10)
        self.lbl_preview = ctk.CTkLabel(
            self.preview_inner, text="💡  Enter fee and select installments to see schedule",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color=(ORANGE, "#fdba74"), anchor="w",
        )
        self.lbl_preview.pack(fill="x")

        self.var_freq.trace_add("write", self._update_preview)
        self.ent_fee.bind("<KeyRelease>", lambda _: self._update_preview())
        self.de_admission.bind("<<DateEntrySelected>>", lambda _: self._update_preview())
        self.ent_discount.bind("<KeyRelease>", lambda _: self._update_preview())

        # Custom per-installment amount frame (appears dynamically)
        self.custom_inst_frame = ctk.CTkFrame(inn, fg_color="transparent")
        self.custom_inst_frame.pack(fill="x", pady=(4, 0))
        self._custom_inst_entries   = []  # list of CTkEntry (amount)
        self._custom_inst_pay_modes = []  # list of StringVar (when to pay)

        # ── Action Buttons ───────────────────────────────────────────────
        bf = ctk.CTkFrame(inn, fg_color="transparent")
        bf.pack(fill="x", pady=(18, 0))

        ctk.CTkButton(
            bf, text="✔  Register Student", height=46, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._submit,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bf, text="Clear Form", height=46, corner_radius=10,
            fg_color="transparent", border_width=1,
            border_color=("#e2e8f0", "#3f3f46"),
            text_color=("#3f3f46", "#d4d4d8"),
            hover_color=("#f4f4f5", "#27272a"),
            command=self._clear,
        ).pack(side="left")

        # Status label
        self.lbl_status = ctk.CTkLabel(inn, text="", font=ctk.CTkFont(size=13), anchor="w")
        self.lbl_status.pack(fill="x", pady=(10, 0))

    # ── Helpers ────────────────────────────────────────────────────────── #

    def _section(self, p, text):
        parts = text.split("  ", 1)
        icon  = parts[0].strip()
        label = parts[1].strip() if len(parts) > 1 else icon
        f = ctk.CTkFrame(p, fg_color="transparent")
        f.pack(fill="x", pady=(18, 6))
        ctk.CTkLabel(
            f, text=icon,
            font=ctk.CTkFont(family="Segoe Fluent Icons", size=16),
            text_color=ORANGE, anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            f, text=label,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w",
        ).pack(side="left", padx=(8, 0))
        ctk.CTkFrame(p, height=1, fg_color=("#e2e8f0", "#27272a")).pack(fill="x", pady=(0, 8))

    def _row(self, p):
        f = ctk.CTkFrame(p, fg_color="transparent")
        f.pack(fill="x", pady=6)
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        return f

    def _label(self, p, text):
        ctk.CTkLabel(
            p, text=text,
            font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8"), anchor="w",
        ).pack(anchor="w", pady=(0, 4))

    def _entry(self, row, col, label, placeholder) -> ctk.CTkEntry:
        f = ctk.CTkFrame(row, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=(0, 8) if col == 0 else (8, 0))
        self._label(f, label)
        e = ctk.CTkEntry(
            f, placeholder_text=placeholder, height=42, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        e.pack(fill="x")
        return e

    def _date_picker(self, row, col, label):
        f = ctk.CTkFrame(row, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=(0, 8) if col == 0 else (8, 0))
        self._label(f, label)
        container = ctk.CTkFrame(f, fg_color="transparent", height=42)
        container.pack(fill="x")
        container.pack_propagate(False)
        de = DateEntry(
            container, width=12,
            background=ORANGE, foreground="white", borderwidth=0,
            font=("Segoe UI", 12), date_pattern="yyyy-mm-dd",
            headersbackground=NAVY, headersforeground="white",
            selectbackground=ORANGE_HOV, normalbackground="#ffffff",
            normalforeground="#0f172a", bottombackground="#f8fafc",
            weekendbackground="#f8fafc", weekendforeground="#dc2626",
        )
        de.pack(fill="both", expand=True, pady=2)
        return de

    def _dropdown(self, row, col, label, values, var):
        f = ctk.CTkFrame(row, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=(0, 8) if col == 0 else (8, 0))
        self._label(f, label)
        ctk.CTkOptionMenu(
            f, values=values, variable=var, height=42, corner_radius=8,
            fg_color=("#f8fafc", NAVY),
            button_color=ORANGE, button_hover_color=ORANGE_HOV,
        ).pack(fill="x")

    def _update_preview(self, *_):
        DISC_DEFAULTS = {1: 3.0, 2: 2.0}  # defaults, overridden by ent_discount
        from utils.fee_calculator import compute_due_dates

        for w in self.preview_inner.winfo_children():
            w.destroy()
        for w in self.custom_inst_frame.winfo_children():
            w.destroy()
        self._custom_inst_entries   = []
        self._custom_inst_pay_modes = []

        try:
            fee   = float(self.ent_fee.get().strip() or 0)
            dur   = self.COURSE_TYPE_MONTHS.get(self.var_ctype.get(), 12)
            n_str = self.var_freq.get()
            n     = max(1, min(12, int(n_str))) if n_str.isdigit() else 1
            adm   = str(self.de_admission.get_date())
            due_dates = compute_due_dates(n, adm, dur)

            # Discount — read from field first, fallback to auto-defaults
            try:
                disc_pct = float(self.ent_discount.get().strip() or 0)
            except (ValueError, AttributeError):
                disc_pct = DISC_DEFAULTS.get(n, 0.0)

            # Auto-fill discount field with default when n changes
            try:
                current = float(self.ent_discount.get().strip() or -1)
                if current < 0:
                    disc_pct = DISC_DEFAULTS.get(n, 0.0)
                    self.ent_discount.delete(0, "end")
                    self.ent_discount.insert(0, f"{disc_pct:.1f}")
            except Exception:
                disc_pct = DISC_DEFAULTS.get(n, 0.0)

            disc_amt  = round(fee * disc_pct / 100, 2)
            effective = round(fee - disc_amt, 2)
            per       = round(effective / n, 2) if n else 0

            # Update discount info label
            if disc_pct > 0:
                self.lbl_disc_info.configure(
                    text=f"Save ₹{disc_amt:,.2f}  →  Payable ₹{effective:,.2f}")
            else:
                self.lbl_disc_info.configure(text="No discount")

            label = "installment" if n == 1 else "installments"

            # Summary in preview box
            ctk.CTkLabel(self.preview_inner,
                text=f"💡  {n} {label}  •  Fee ₹{fee:,.2f}  •  {disc_pct:.1f}% off  •  Payable ₹{effective:,.2f}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=(ORANGE, "#fdba74"), anchor="w",
            ).pack(fill="x")

            # Installment date schedule
            for i, dd in enumerate(due_dates):
                if n == 2:
                    note = "at admission" if i == 0 else "+3 months"
                else:
                    note = "at admission" if i == 0 else f"+{i * max(1, dur // n)} months"
                ctk.CTkLabel(self.preview_inner,
                    text=f"     📅 #{i+1} → {dd.strftime('%b %d, %Y')}  ({note})",
                    font=ctk.CTkFont(size=11),
                    text_color=("#92400e", "#fcd34d"), anchor="w",
                ).pack(fill="x")

            # Per-installment amount + pay mode rows
            if n > 0:
                ctk.CTkLabel(self.custom_inst_frame,
                    text="✏️  Installment Amounts & Payment Timing",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=("#475569", "#94a3b8"), anchor="w",
                ).pack(fill="x", pady=(8, 2))
                ctk.CTkLabel(self.custom_inst_frame,
                    text="  Last installment auto-adjusts to cover remaining payable amount",
                    font=ctk.CTkFont(size=10),
                    text_color=("#64748b", "#6b7280"), anchor="w",
                ).pack(fill="x", pady=(0, 4))

                for i in range(n):
                    is_last = (i == n - 1)
                    row_f = ctk.CTkFrame(self.custom_inst_frame,
                        fg_color=("#f8fafc", NAVY_LIGHT), corner_radius=8,
                        border_width=1 if is_last else 0,
                        border_color=("#86efac", "#166534") if is_last else "transparent")
                    row_f.pack(fill="x", pady=2)
                    row_f.columnconfigure(1, weight=1)

                    # #N label
                    num_lbl = ctk.CTkFrame(row_f, fg_color=ORANGE if not is_last else "#059669",
                        corner_radius=6, width=44, height=30)
                    num_lbl.pack_propagate(False)
                    num_lbl.grid(row=0, column=0, padx=(10, 6), pady=8)
                    ctk.CTkLabel(num_lbl, text=f"#{i+1}",
                        font=ctk.CTkFont(size=11, weight="bold"), text_color="white"
                    ).pack(expand=True)

                    # Amount entry (now all are editable)
                    e = ctk.CTkEntry(row_f, height=34, corner_radius=8,
                        border_width=1, border_color=("#e2e8f0", "#334155"),
                        state="normal")
                    e.insert(0, f"{per:.2f}")
                    e.grid(row=0, column=1, sticky="ew", padx=(0, 8))
                    self._custom_inst_entries.append(e)

                    # Auto-update last entry when others change
                    if not is_last:
                        def on_change(*_, idx=i, entries=self._custom_inst_entries,
                                      tot=effective, num=n, last_e=None):
                            self._recalc_last(tot, num)
                        e.bind("<KeyRelease>", on_change)

                    # When to pay
                    PAY_MODES = ["Pending", "Pay Now", "In 1 Week"]
                    default   = "Pay Now" if i == 0 else "Pending"
                    mv = ctk.StringVar(value=default)
                    self._custom_inst_pay_modes.append(mv)
                    ctk.CTkOptionMenu(row_f, values=PAY_MODES, variable=mv,
                        width=120, height=34, corner_radius=8,
                        fg_color=("#f1f5f9", NAVY),
                        button_color=ORANGE if not is_last else "#059669",
                        button_hover_color=ORANGE_HOV if not is_last else "#047857",
                    ).grid(row=0, column=2, padx=(0, 10))

        except Exception:
            ctk.CTkLabel(self.preview_inner,
                text="💡  Enter fee and select installments to see schedule",
                font=ctk.CTkFont(size=12),
                text_color=(ORANGE, "#fdba74"), anchor="w",
            ).pack(fill="x")

    def _recalc_last(self, effective: float, n: int):
        """Auto-update the last installment entry = effective - sum of others."""
        if len(self._custom_inst_entries) < n:
            return
        try:
            paid_so_far = sum(
                float(self._custom_inst_entries[i].get().strip() or 0)
                for i in range(n - 1)
            )
            remaining = round(effective - paid_so_far, 2)
            last = self._custom_inst_entries[n - 1]
            last.delete(0, "end")
            last.insert(0, f"{max(0, remaining):.2f}")
        except Exception:
            pass

    # ── Logic ──────────────────────────────────────────────────────────── #

    def _submit(self):
        name         = self.ent_name.get().strip()
        father_name  = self.ent_father_name.get().strip()
        dob          = str(self.de_dob.get_date())
        address      = self.txt_address.get("1.0", "end").strip()
        course       = self.var_course.get()
        phone        = self.ent_phone.get().strip()
        parent_phone = self.ent_parent_phone.get().strip()
        gender       = self.var_gender.get()
        category     = self.var_category.get()
        course_type  = self.var_ctype.get()

        # Gather checked subjects
        selected_subjects = [subj for subj, var in self.subj_vars.items() if var.get() == "on"]
        subjects_str = ", ".join(selected_subjects)

        fee_str  = self.ent_fee.get().strip()
        freq     = self.var_freq.get()
        adm_date = str(self.de_admission.get_date())
        dur      = self.COURSE_TYPE_MONTHS.get(course_type, 12)

        if not all([name, father_name, dob, address, fee_str, adm_date]):
            self.lbl_status.configure(text="⚠  All required fields must be filled.", text_color="#dc2626")
            return
        try:
            fee = float(fee_str)
            if fee <= 0:
                raise ValueError
        except ValueError:
            self.lbl_status.configure(
                text="⚠  Fee must be a positive number.", text_color="#dc2626"
            )
            return

        try:
            from utils.fee_calculator import compute_due_dates
            n_inst = int(freq) if freq.isdigit() else 1
            try:
                disc_pct = float(self.ent_discount.get().strip() or 0)
            except (ValueError, AttributeError):
                disc_pct = {1: 3.0, 2: 2.0}.get(n_inst, 0.0)
            effective = round(fee * (1 - disc_pct / 100), 2)

            # Read custom installment amounts if provided
            custom_amts = []
            for e in self._custom_inst_entries:
                try:
                    custom_amts.append(float(e.get().strip() or 0))
                except ValueError:
                    custom_amts.append(0)

            # Combine phone info — safely truncated to 58 chars
            phone_combined = phone
            if parent_phone:
                phone_combined = f"{phone} / P:{parent_phone}"
            phone_combined = phone_combined[:58]  # Guard against DB column limit
            sid = self.db.add_student(name, father_name, dob, address, course,
                                      fee, dur, freq, adm_date, phone_combined,
                                      subjects_str, gender, category, course_type)
            # Auto-create installment schedule with custom amounts
            try:
                from datetime import date as _date, timedelta
                due_dates = compute_due_dates(n_inst, adm_date, dur)
                if custom_amts and len(custom_amts) == n_inst and all(a > 0 for a in custom_amts):
                    self.db.create_installment_schedule_custom(sid, due_dates, custom_amts)
                else:
                    amt_each = round(effective / n_inst, 2)
                    self.db.create_installment_schedule_custom(
                        sid, due_dates, [amt_each] * n_inst)

                # Process per-installment payment modes
                insts = self.db.get_installments(sid)
                today = str(_date.today())
                for idx, inst in enumerate(insts):
                    if idx >= len(self._custom_inst_pay_modes):
                        break
                    mode = self._custom_inst_pay_modes[idx].get()
                    amt  = float(inst['amount_due'])
                    if mode == "Pay Now":
                        self.db.record_installment_payment(inst['id'], amt, today)
                    elif mode == "In 1 Week":
                        from datetime import date as _d2, timedelta as _td
                        split_dt = str(_d2.today() + _td(days=7))
                        self.db.mark_installment_split(inst['id'], split_dt)
            except Exception as e:
                print(f"[Admission] Schedule warning: {e}")

            self.lbl_status.configure(
                text=f"✔  Student registered! (ID: #{sid:03d})  —  Switching to Manage Installments…",
                text_color="#059669",
            )
            self._clear()
            # Auto-switch to installments tab so they can see the new schedule
            self.after(600, lambda: self._switch_tab("installments"))
            if self.on_success:
                self.on_success()
        except Exception as e:
            self.lbl_status.configure(text=f"✖  {e}", text_color="#dc2626")

    def _clear(self):
        for e in (self.ent_name, self.ent_father_name, self.ent_phone,
                  self.ent_parent_phone, self.ent_fee):
            e.delete(0, "end")
        self.de_dob.set_date(date.today())
        self.de_admission.set_date(date.today())
        self.txt_address.delete("1.0", "end")
        for var in self.subj_vars.values():
            var.set("off")
        self.var_course.set(self.COURSES[0])
        self.var_freq.set("2")
        self.var_ctype.set(self.COURSE_TYPES[0])
        self.var_gender.set(self.GENDERS[0])
        self.var_category.set(self.CATEGORIES[0])
        self.lbl_status.configure(text="")
        self._custom_inst_pay_modes = []
        self._update_preview()
            
    def _update_subjects_ui(self, *args):
        # Clear existing subjects
        for widget in self.subj_frame.winfo_children():
            widget.destroy()
        self.subj_vars.clear()
        
        course = self.var_course.get()
        subjects = self.COURSE_SUBJECTS.get(course, [])
        
        if subjects:
            ctk.CTkLabel(
                self.subj_frame, text="\uE734  Select Applicable Subjects:",
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
                text_color=("#64748b", "#94a3b8")
            ).pack(anchor="w", pady=(5, 5))
            
            chk_frame = ctk.CTkFrame(self.subj_frame, fg_color="transparent")
            chk_frame.pack(fill="x")
            
            col = 0
            row = 0
            for subj in subjects:
                var = ctk.StringVar(value="off")
                self.subj_vars[subj] = var
                chk = ctk.CTkCheckBox(
                    chk_frame, text=subj, variable=var, onvalue="on", offvalue="off",
                    font=ctk.CTkFont(size=12), fg_color=ORANGE, hover_color=ORANGE_HOV
                )
                chk.grid(row=row, column=col, padx=(0, 15), pady=5, sticky="w")
                col += 1
                if col > 3: # 4 columns
                    col = 0
                    row += 1

    def refresh(self):
        """Called when navigating to this page — refresh installments tab data."""
        try:
            self.frame_installments.refresh()
        except Exception:
            pass
