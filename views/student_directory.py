"""
views/student_directory.py
--------------------------
Student Directory — Srijan Institute theme (Navy + Reddish-Orange).
Features: search, full-details popup, DELETE student with confirmation.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.fee_calculator import calculate_installments, summary

# ── Institute Palette ──────────────────────────────────────────────────────
ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class StudentDirectoryView(ctk.CTkFrame):
    def __init__(self, parent, db_manager):
        super().__init__(parent, fg_color="transparent")
        self.db = db_manager
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────── #

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Student Directory",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="All enrolled students — search, view details, or remove records",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 16)
        )

        # Search bar
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=30, pady=(0, 12))
        sf.columnconfigure(0, weight=1)

        self.var_search = ctk.StringVar()
        self.var_search.trace_add("write", lambda *_: self.refresh())

        ctk.CTkEntry(
            sf, textvariable=self.var_search,
            placeholder_text="\uE721  Search by name or ID…",
            height=42, corner_radius=10,
            border_width=1, border_color=("#e2e8f0", "#3f3f46"),
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(
            sf, text="\uE721  Search", width=110, height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self.refresh,
        ).grid(row=0, column=1)

        # Table card
        table_frame = ctk.CTkFrame(
            self, fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=14, border_width=1,
            border_color=("#e2e8f0", "#334155"),
        )
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 0))

        # Treeview styling
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Dir.Treeview",
            background=NAVY_LIGHT, foreground="#e2e8f0",
            rowheight=40, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Dir.Treeview.Heading",
            background=NAVY, foreground="#94a3b8",
            relief="flat", font=("Segoe UI", 11, "bold"), padding=(6, 10),
        )
        style.map(
            "Dir.Treeview",
            background=[("selected", ORANGE)],
            foreground=[("selected", "white")],
        )

        cols = ("id", "name", "course", "admission_date", "total_paid", "balance")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", style="Dir.Treeview"
        )

        headers = {
            "id": ("ID", 65, "center"),
            "name": ("Student Name", 220, "w"),
            "course": ("Course / Class", 150, "w"),
            "admission_date": ("Admission Date", 130, "center"),
            "total_paid": ("Total Paid", 130, "e"),
            "balance": ("Balance", 130, "e"),
        }
        for col, (text, width, anchor) in headers.items():
            self.tree.heading(col, text=text, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor)

        scroll = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

        self.tree.bind("<Double-1>", self._show_details)
        self.tree.bind("<Return>", self._show_details)
        self.tree.tag_configure("cleared", foreground="#10b981")
        self.tree.tag_configure("defaulter", foreground="#f87171")

        # Action bar
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=30, pady=(10, 20))

        ctk.CTkLabel(
            action_frame,
            text="💡  Double-click a student to view full details",
            font=ctk.CTkFont(size=12), text_color="#64748b",
        ).pack(side="left")

        ctk.CTkButton(
            action_frame, text="\uE7BA  Delete Student",
            width=150, height=38, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
            command=self._confirm_delete,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            action_frame, text="\uE8A5  View Details",
            width=140, height=38, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._show_details,
        ).pack(side="right")

    # ── Data ───────────────────────────────────────────────────────────── #

    def refresh(self):
        try:
            query = self.var_search.get().strip()
            data  = self.db.search_students(query) if query else self.db.get_all_students()
            self.tree.delete(*self.tree.get_children())
            for row in data:
                bal = float(row["balance"])
                tag = "cleared" if bal <= 0 else ("defaulter" if bal == float(row.get("total_course_fee", 0)) else "")
                self.tree.insert("", "end", iid=row["id"], values=(
                    f"#{row['id']:03d}",
                    row["name"],
                    row["course"],
                    str(row.get("admission_date", "N/A")),
                    f"₹{float(row['total_paid']):,.0f}",
                    f"₹{bal:,.0f}",
                ), tags=(tag,))
        except Exception as e:
            print(f"[Directory] Load error: {e}")

    # ── Delete ─────────────────────────────────────────────────────────── #

    def _confirm_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a student to delete.")
            return

        student_id = int(selected[0])
        try:
            student = self.db.get_student_by_id(student_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        if not student:
            return

        # Confirmation modal
        modal = ctk.CTkToplevel(self)
        modal.title("Confirm Deletion")
        modal.geometry("480x280")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.configure(fg_color=NAVY)

        # Warning icon + title
        ctk.CTkLabel(
            modal, text="⚠",
            font=ctk.CTkFont(size=42), text_color="#ef4444",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            modal, text="Delete Student Record",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold"),
            text_color="white",
        ).pack()

        ctk.CTkLabel(
            modal,
            text=f'This will permanently delete "{student["name"]}" (ID #{student_id:03d})\nand ALL their payment records. This cannot be undone.',
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#94a3b8", justify="center",
        ).pack(pady=(10, 24))

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack()

        def do_delete():
            try:
                self.db.delete_student(student_id)
                modal.destroy()
                self.refresh()
                messagebox.showinfo(
                    "Deleted",
                    f'Student "{student["name"]}" has been removed successfully.',
                )
            except Exception as ex:
                modal.destroy()
                messagebox.showerror("Delete Failed", str(ex))

        ctk.CTkButton(
            btn_row, text="Yes, Delete Permanently",
            width=200, height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
            command=do_delete,
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_row, text="Cancel",
            width=110, height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13),
            fg_color="transparent", border_width=1, border_color="#334155",
            text_color="#94a3b8", hover_color="#1e293b",
            command=modal.destroy,
        ).pack(side="left")

    # ── Details Popup ──────────────────────────────────────────────────── #

    def _show_details(self, event=None):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a student.")
            return
        student_id = int(selected[0])
        try:
            student  = self.db.get_student_by_id(student_id)
            payments = self.db.get_payments_for_student(student_id)
            if not student:
                return
            self._open_master_popup(student, payments)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load details: {e}")

    def _open_master_popup(self, student, payments):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Student Details — {student['name']}")
        modal.geometry("780x680")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Header banner
        banner = ctk.CTkFrame(scroll, fg_color=(ORANGE, ORANGE_HOV), corner_radius=14)
        banner.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            banner, text="\uE77B",
            font=ctk.CTkFont(family="Segoe Fluent Icons", size=44),
            text_color="white",
        ).pack(side="left", padx=(20, 10), pady=20)

        info = ctk.CTkFrame(banner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=20)
        ctk.CTkLabel(
            info, text=student["name"],
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=22, weight="bold"),
            text_color="white", anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text=f"ID: #{student['id']:03d}  ·  {student['course']}",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13),
            text_color="#fde8d8", anchor="w",
        ).pack(fill="x")

        # Two-column layout
        cols = ctk.CTkFrame(scroll, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)

        # Personal info card
        left = ctk.CTkFrame(
            cols, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            left, text="Personal Information",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
            text_color=(ORANGE, "#fb923c"),
        ).pack(anchor="w", padx=20, pady=(18, 10))
        ctk.CTkFrame(left, height=1, fg_color=("#e2e8f0", "#334155")).pack(fill="x", padx=20, pady=(0, 8))

        self._detail_row(left, "Father's Name", student["father_name"])
        self._detail_row(left, "Date of Birth",  str(student["dob"]))
        self._detail_row(left, "Admission Date", str(student.get("admission_date", "N/A")))
        self._detail_row(left, "Duration", f"{student.get('course_duration_months', 12)} months")
        self._detail_row(left, "Frequency", student.get("fee_frequency", "Monthly"))
        self._detail_row(left, "Address", student["address"])

        # Financial card
        right = ctk.CTkFrame(
            cols, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            right, text="Financial Status",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
            text_color=(ORANGE, "#fb923c"),
        ).pack(anchor="w", padx=20, pady=(18, 10))
        ctk.CTkFrame(right, height=1, fg_color=("#e2e8f0", "#334155")).pack(fill="x", padx=20, pady=(0, 8))

        installments = calculate_installments(student, payments)
        stats        = summary(installments)
        total_fee    = float(student["total_course_fee"])
        total_paid   = float(student["total_paid"])
        balance      = total_fee - total_paid
        overdue_insts = [i for i in installments if i["status"] == "OVERDUE"]
        overdue_amt   = sum(i["amount_due"] - i["amount_paid"] for i in overdue_insts)

        self._detail_row(right, "Total Course Fee", f"₹{total_fee:,.0f}")
        self._detail_row(right, "Total Paid",       f"₹{total_paid:,.0f}", color="#10b981")
        self._detail_row(right, "Balance",          f"₹{balance:,.0f}")
        ctk.CTkFrame(right, height=1, fg_color=("#e2e8f0", "#334155")).pack(fill="x", padx=20, pady=8)
        self._detail_row(right, "Months Paid", f"{stats['paid_n']} / {stats['n_inst']}")

        if overdue_amt > 0:
            self._detail_row(right, "Overdue Amount", f"₹{overdue_amt:,.0f}", color="#ef4444")
            self._detail_row(right, "Status", "⚠  Defaulter", color="#ef4444")
        elif balance <= 0:
            self._detail_row(right, "Status", "✅  Fully Cleared", color="#10b981")
        else:
            self._detail_row(right, "Status", "✔  On Track", color="#3b82f6")

        # Recent payments
        if payments:
            rec = ctk.CTkFrame(
                scroll, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=14,
                border_width=1, border_color=("#e2e8f0", "#334155"),
            )
            rec.pack(fill="x", pady=(16, 0))
            ctk.CTkLabel(
                rec, text="Recent Payments",
                font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
                text_color=(ORANGE, "#fb923c"),
            ).pack(anchor="w", padx=20, pady=(18, 8))
            ctk.CTkFrame(rec, height=1, fg_color=("#e2e8f0", "#334155")).pack(fill="x", padx=20, pady=(0, 8))
            for p in payments[:6]:
                p_row = ctk.CTkFrame(
                    rec, fg_color=("#f8fafc", NAVY), corner_radius=8,
                )
                p_row.pack(fill="x", padx=20, pady=4)
                ctk.CTkLabel(
                    p_row, text=f"  {p['payment_date']}",
                    font=ctk.CTkFont(size=12), text_color=("#475569", "#94a3b8"),
                ).pack(side="left", padx=4, pady=8)
                ctk.CTkLabel(
                    p_row, text=f"({p['month_name']})",
                    font=ctk.CTkFont(size=12), text_color=("#64748b", "#64748b"),
                ).pack(side="left", padx=4)
                ctk.CTkLabel(
                    p_row, text=f"₹{float(p['amount_paid']):,.0f}  ",
                    font=ctk.CTkFont(size=13, weight="bold"), text_color="#10b981",
                ).pack(side="right", padx=4)
            ctk.CTkFrame(rec, height=12, fg_color="transparent").pack()

    def _detail_row(self, parent, label, value, color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(
            row, text=label,
            font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8"),
        ).pack(side="left")
        ctk.CTkLabel(
            row, text=value,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color if color else (("#0f172a"), "white"),
        ).pack(side="right")
