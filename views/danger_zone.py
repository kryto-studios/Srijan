"""
views/danger_zone.py
---------------------
Danger Zone — clear all student data after admin password verification.
"""

import customtkinter as ctk
from tkinter import messagebox

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"
RED        = "#dc2626"
RED_HOV    = "#b91c1c"
RED_DIM    = "#450a0a"


class DangerZoneView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        # ── Page Header ──
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(22, 6))
        ctk.CTkLabel(hdr, text="⚠  Danger Zone",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
            text_color=RED,
        ).pack(anchor="w")
        ctk.CTkLabel(hdr,
            text="Irreversible actions — read carefully before proceeding",
            font=ctk.CTkFont(size=12), text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=RED_DIM).pack(fill="x", padx=30, pady=(6, 20))

        # ── Warning card ──
        card = ctk.CTkFrame(self, fg_color=RED_DIM, corner_radius=14,
                            border_width=2, border_color=RED)
        card.pack(fill="x", padx=30, pady=(0, 20))

        icon_row = ctk.CTkFrame(card, fg_color="transparent")
        icon_row.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(icon_row, text="🗑",
            font=ctk.CTkFont(size=32),
        ).pack(side="left", padx=(0, 12))
        title_col = ctk.CTkFrame(icon_row, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_col, text="Clear All Student Data",
            font=ctk.CTkFont(size=17, weight="bold"), text_color="#fca5a5", anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(title_col,
            text="Permanently deletes ALL students, their installments, payments, and invoices.",
            font=ctk.CTkFont(size=11), text_color="#f87171", anchor="w", wraplength=480, justify="left",
        ).pack(anchor="w", pady=(2, 0))

        # What gets deleted checklist
        info = ctk.CTkFrame(card, fg_color="#3b0a0a", corner_radius=8)
        info.pack(fill="x", padx=24, pady=(4, 16))
        for line in [
            "✖  All student profiles and Member IDs",
            "✖  All installment schedules",
            "✖  All payment records",
            "✖  All invoices",
            "✔  Admin/user login credentials (kept safe)",
        ]:
            color = "#fca5a5" if line.startswith("✖") else "#86efac"
            ctk.CTkLabel(info, text=f"  {line}",
                font=ctk.CTkFont(size=12), text_color=color, anchor="w",
            ).pack(fill="x", padx=14, pady=3)

        # ── Auth section ──
        auth = ctk.CTkFrame(card, fg_color="transparent")
        auth.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkLabel(auth, text="Enter your Username:",
            font=ctk.CTkFont(size=12), text_color="#94a3b8", anchor="w",
        ).pack(fill="x")
        self.ent_user = ctk.CTkEntry(auth, placeholder_text="admin username",
            height=38, corner_radius=8,
            border_width=1, border_color="#7f1d1d",
        )
        self.ent_user.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(auth, text="Enter your Password:",
            font=ctk.CTkFont(size=12), text_color="#94a3b8", anchor="w",
        ).pack(fill="x")
        self.ent_pass = ctk.CTkEntry(auth, placeholder_text="admin password",
            height=38, corner_radius=8, show="●",
            border_width=1, border_color="#7f1d1d",
        )
        self.ent_pass.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(auth,
            text='Type  CONFIRM DELETE  exactly in the box below to proceed:',
            font=ctk.CTkFont(size=12), text_color="#f87171", anchor="w",
        ).pack(fill="x")
        self.ent_confirm = ctk.CTkEntry(auth, placeholder_text="CONFIRM DELETE",
            height=38, corner_radius=8,
            border_width=1, border_color="#7f1d1d",
        )
        self.ent_confirm.pack(fill="x", pady=(4, 0))

        self.lbl_status = ctk.CTkLabel(auth, text="",
            font=ctk.CTkFont(size=12), anchor="w",
        )
        self.lbl_status.pack(fill="x", pady=(8, 0))

        # ── Action button ──
        ctk.CTkButton(card,
            text="🗑  ERASE ALL STUDENT DATA",
            height=46, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=RED, hover_color=RED_HOV,
            command=self._confirm_and_clear,
        ).pack(fill="x", padx=24, pady=(0, 24))

    def _confirm_and_clear(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()
        confirm  = self.ent_confirm.get().strip()

        # Step 1: check confirmation phrase
        if confirm != "CONFIRM DELETE":
            self.lbl_status.configure(
                text='⚠  Type exactly: CONFIRM DELETE', text_color="#f97316")
            return

        # Step 2: verify admin credentials
        user = self.db.authenticate(username, password)
        if not user:
            self.lbl_status.configure(
                text="✖  Invalid username or password.", text_color=RED)
            return

        # Step 3: final messagebox double-check
        ok = messagebox.askyesno(
            "⚠ FINAL WARNING",
            f"You are about to permanently delete ALL student data.\n\n"
            f"This CANNOT be undone.\n\nProceed?",
            icon="warning",
            parent=self,
        )
        if not ok:
            self.lbl_status.configure(text="Cancelled.", text_color="#64748b")
            return

        # Step 4: execute
        try:
            count = self.db.clear_all_student_data()
            self.ent_user.delete(0, "end")
            self.ent_pass.delete(0, "end")
            self.ent_confirm.delete(0, "end")
            self.lbl_status.configure(
                text=f"✔  Done. {count} student record(s) erased.",
                text_color="#10b981",
            )
            messagebox.showinfo(
                "Cleared",
                f"✔ {count} student record(s) and all related data have been permanently deleted.",
                parent=self,
            )
        except Exception as e:
            self.lbl_status.configure(text=f"✖  Error: {e}", text_color=RED)
