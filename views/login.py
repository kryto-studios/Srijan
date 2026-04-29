"""
views/login.py
--------------
Secure authentication screen for Srijan Institute.
"""

import customtkinter as ctk
from PIL import Image

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, db, on_success, **kwargs):
        super().__init__(parent, fg_color=("#0f172a", "#020617"), **kwargs)
        self.db = db
        self.on_success = on_success
        self._build_ui()

    def _build_ui(self):
        # Split screen layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=4) # Left branding panel
        self.grid_columnconfigure(1, weight=5) # Right login panel

        # ── Left Branding Panel ─────────────────────────────────────────
        left_panel = ctk.CTkFrame(self, fg_color=("#1e293b", "#0f172a"), corner_radius=0)
        left_panel.grid(row=0, column=0, sticky="nsew")
        left_panel.grid_rowconfigure((0, 2), weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        brand_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        brand_frame.grid(row=1, column=0)
        
        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open("assets/logo.png"),
                dark_image=Image.open("assets/logo.png"),
                size=(160, 115)
            )
            ctk.CTkLabel(brand_frame, image=logo_img, text="").pack(pady=(0, 20))
        except Exception:
            ctk.CTkLabel(
                brand_frame, text="\uE835",
                font=ctk.CTkFont(family="Segoe Fluent Icons", size=72),
                text_color="#c2410c"
            ).pack(pady=(0, 20))
            
        ctk.CTkLabel(
            brand_frame, text="Srijan Institute",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=34, weight="bold"),
            text_color="white"
        ).pack()
        ctk.CTkLabel(
            brand_frame, text="Student Fee Management System",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14),
            text_color="#94a3b8"
        ).pack(pady=(5, 0))

        # ── Right Login Panel ───────────────────────────────────────────
        right_panel = ctk.CTkFrame(self, fg_color=("#f8fafc", "#020617"), corner_radius=0)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure((0, 2), weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Elevated Card
        card = ctk.CTkFrame(
            right_panel, corner_radius=16,
            fg_color=("#ffffff", "#1e293b"),
            border_width=1, border_color=("#e2e8f0", "#334155")
        )
        card.grid(row=1, column=0, padx=40)
        
        # Title
        ctk.CTkLabel(
            card, text="Welcome Back",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
            text_color=("#0f172a", "white")
        ).pack(pady=(40, 5))
        
        ctk.CTkLabel(
            card, text="Please enter your secure credentials to continue",
            font=ctk.CTkFont(size=13), text_color="#64748b"
        ).pack(pady=(0, 30))

        # Username Input
        ctk.CTkLabel(
            card, text="USERNAME", 
            font=ctk.CTkFont(size=11, weight="bold"), text_color=("#64748b", "#94a3b8")
        ).pack(anchor="w", padx=45)
        
        self.ent_user = ctk.CTkEntry(
            card, placeholder_text="admin", width=340, height=48,
            corner_radius=8, border_width=1, border_color=("#cbd5e1", "#475569"),
            fg_color=("#f8fafc", "#0f172a"), text_color=("#0f172a", "white"),
            font=ctk.CTkFont(size=14)
        )
        self.ent_user.pack(pady=(5, 20), padx=45)
        
        # Password Input
        ctk.CTkLabel(
            card, text="PASSWORD", 
            font=ctk.CTkFont(size=11, weight="bold"), text_color=("#64748b", "#94a3b8")
        ).pack(anchor="w", padx=45)
        
        self.ent_pass = ctk.CTkEntry(
            card, placeholder_text="••••••••", width=340, height=48, show="•",
            corner_radius=8, border_width=1, border_color=("#cbd5e1", "#475569"),
            fg_color=("#f8fafc", "#0f172a"), text_color=("#0f172a", "white"),
            font=ctk.CTkFont(size=14)
        )
        self.ent_pass.pack(pady=(5, 10), padx=45)
        
        # Error text
        self.lbl_error = ctk.CTkLabel(card, text="", text_color="#ef4444", font=ctk.CTkFont(size=12))
        self.lbl_error.pack(pady=(0, 10))

        # Submit Button
        self.btn_login = ctk.CTkButton(
            card, text="Sign In \u2192", width=340, height=50, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
            fg_color="#c2410c", hover_color="#9a3412",
            command=self._do_login
        )
        self.btn_login.pack(pady=(10, 45), padx=45)
        
        self.ent_pass.bind("<Return>", lambda e: self._do_login())
        self.ent_user.bind("<Return>", lambda e: self.ent_pass.focus())

    def _do_login(self):
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get().strip()
        
        if not user or not pwd:
            self.lbl_error.configure(text="Please enter credentials")
            return
            
        self.lbl_error.configure(text="Authenticating...", text_color="#3b82f6")
        self.btn_login.configure(state="disabled")
        
        try:
            user_data = self.db.authenticate(user, pwd)
            if user_data:
                self.on_success(user_data)
            else:
                self.lbl_error.configure(text="Invalid credentials", text_color="#ef4444")
                self.btn_login.configure(state="normal")
        except Exception as e:
            self.lbl_error.configure(text=f"Error: {e}", text_color="#ef4444")
            self.btn_login.configure(state="normal")
