"""
views/add_student.py
--------------------
Student registration form — Srijan Institute theme (Navy + Reddish-Orange).
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
from utils.fee_calculator import FREQUENCIES
from tkcalendar import DateEntry

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

    def __init__(self, parent, db, on_success=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db         = db
        self.on_success = on_success
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────── #

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Register New Student",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="Fill in all fields below to enroll a new student",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 20)
        )

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
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
        self.de_dob = self._date_picker(r2, 0, "Date of Birth *")
        self.var_course = ctk.StringVar(value=self.COURSES[0])
        self._dropdown(r2, 1, "Course / Class *", self.COURSES, self.var_course)

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
        self.ent_fee      = self._entry(r3, 0, "Total Course Fee (₹) *", "e.g. 45000")
        self.ent_duration = self._entry(r3, 1, "Course Duration (Months) *", "e.g. 12")

        r4 = self._row(inn)
        self.var_freq = ctk.StringVar(value="Monthly")
        self._dropdown(r4, 0, "Fee Frequency *", FREQUENCIES, self.var_freq)
        self.de_admission = self._date_picker(r4, 1, "Admission Date *")

        # ── Fee Preview ──────────────────────────────────────────────────
        prev_frame = ctk.CTkFrame(
            inn, fg_color=("#fff7ed", "#431407"),
            corner_radius=8, border_width=1, border_color=("#fed7aa", "#7c2d12"),
        )
        prev_frame.pack(fill="x", pady=(12, 0))
        self.lbl_preview = ctk.CTkLabel(
            prev_frame, text="💡  Enter fee and duration to see installment preview",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color=(ORANGE, "#fdba74"), anchor="w",
        )
        self.lbl_preview.pack(fill="x", padx=14, pady=10)

        self.var_freq.trace_add("write", self._update_preview)
        self.ent_fee.bind("<KeyRelease>", lambda _: self._update_preview())
        self.ent_duration.bind("<KeyRelease>", lambda _: self._update_preview())

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
        try:
            from utils.fee_calculator import FREQUENCY_MONTHS
            fee  = float(self.ent_fee.get().strip() or 0)
            dur  = int(self.ent_duration.get().strip() or 0)
            freq = self.var_freq.get()
            fm   = FREQUENCY_MONTHS.get(freq, 1)
            n    = max(1, dur // fm) if dur else 0
            per  = fee / n if n else 0
            self.lbl_preview.configure(
                text=f"💡  {n} installment{'s' if n != 1 else ''} of  ₹{per:,.2f}  each  ({freq})"
            )
        except Exception:
            self.lbl_preview.configure(
                text="💡  Enter fee and duration to see installment preview"
            )

    # ── Logic ──────────────────────────────────────────────────────────── #

    def _submit(self):
        name        = self.ent_name.get().strip()
        father_name = self.ent_father_name.get().strip()
        dob         = str(self.de_dob.get_date())
        address     = self.txt_address.get("1.0", "end").strip()
        course      = self.var_course.get()
        fee_str     = self.ent_fee.get().strip()
        dur_str     = self.ent_duration.get().strip()
        freq        = self.var_freq.get()
        adm_date    = str(self.de_admission.get_date())

        if not all([name, father_name, dob, address, fee_str, dur_str, adm_date]):
            self.lbl_status.configure(text="⚠  All fields are required.", text_color="#dc2626")
            return
        try:
            fee = float(fee_str)
            dur = int(dur_str)
            if fee <= 0 or dur <= 0:
                raise ValueError
        except ValueError:
            self.lbl_status.configure(
                text="⚠  Fee and Duration must be positive numbers.", text_color="#dc2626"
            )
            return

        try:
            sid = self.db.add_student(name, father_name, dob, address, course,
                                      fee, dur, freq, adm_date)
            self.lbl_status.configure(
                text=f"✔  Student registered successfully! (ID: #{sid:03d})",
                text_color="#059669",
            )
            self._clear()
            if self.on_success:
                self.on_success()
        except Exception as e:
            self.lbl_status.configure(text=f"✖  {e}", text_color="#dc2626")

    def _clear(self):
        for e in (self.ent_name, self.ent_father_name, self.ent_fee, self.ent_duration):
            e.delete(0, "end")
        self.de_dob.set_date(date.today())
        self.de_admission.set_date(date.today())
        self.txt_address.delete("1.0", "end")
        self.var_course.set(self.COURSES[0])
        self.var_freq.set("Monthly")
        self.lbl_status.configure(text="")
        self.lbl_preview.configure(
            text="💡  Enter fee and duration to see installment preview"
        )
