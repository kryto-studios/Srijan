"""
views/dashboard.py
------------------
Premium Dashboard — Srijan Institute theme (Navy + Reddish-Orange).
Animated counter roll-up, collection progress bar, clickable overdue card.
"""

import customtkinter as ctk

# ── Institute Palette ──────────────────────────────────────────────────────
ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"
CARD_DARK  = "#1e293b"
CARD_LIGHT = "#ffffff"


class DashboardView(ctk.CTkFrame):
    """Statistics dashboard with animated metric cards."""

    CARD_CONFIGS = [
        {
            "title": "Total Students",
            "key":   "total_students",
            "icon":  "\uE77B",
            "color": "#3b82f6",
            "fmt":   lambda v: str(int(v)),
            "suffix": "enrolled",
        },
        {
            "title": "Total Collected",
            "key":   "total_collected",
            "icon":  "\uE825",
            "color": "#10b981",
            "fmt":   lambda v: f"₹{v:,.0f}",
            "suffix": "received",
        },
        {
            "title": "Pending Fees",
            "key":   "total_pending",
            "icon":  "\uE81C",
            "color": ORANGE,
            "fmt":   lambda v: f"₹{v:,.0f}",
            "suffix": "outstanding",
        },
        {
            "title": "Overdue Now",
            "key":   "total_overdue",
            "icon":  "\uE7BA",
            "color": "#ef4444",
            "fmt":   lambda v: f"₹{v:,.0f}",
            "suffix": "click to view",
        },
    ]

    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._stats = {}
        self._build_ui()
        self.refresh()

    # ─────────────────────────────────────────────────────────── Build ── #

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(
            title_frame, text="Dashboard",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame, text="Real-time fee collection overview",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="\uE72C  Refresh",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12, weight="bold"),
            width=120, height=38, corner_radius=10,
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self.refresh,
        ).pack(side="right", pady=10)

        # Divider
        ctk.CTkFrame(self, height=2, fg_color=(("#e2e8f0"), NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 24)
        )

        # ── Stat Cards Row ───────────────────────────────────────────────
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=30)
        self.cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.cards = []
        self._val_labels = []

        for i, cfg in enumerate(self.CARD_CONFIGS):
            card, val_lbl = self._make_card(self.cards_frame, cfg)
            card.grid(row=0, column=i, sticky="ew", padx=8, pady=4)
            self.cards.append(card)
            self._val_labels.append((cfg, val_lbl))

        # ── Collection Progress Bar ─────────────────────────────────────
        prog_frame = ctk.CTkFrame(
            self, fg_color=(CARD_LIGHT, CARD_DARK),
            corner_radius=14, border_width=1,
            border_color=("#e2e8f0", NAVY_LIGHT),
        )
        prog_frame.pack(fill="x", padx=30, pady=(20, 10))

        inner = ctk.CTkFrame(prog_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)
        inner.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            inner, text="Collection Rate",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.lbl_rate = ctk.CTkLabel(
            inner, text="—",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
            text_color=ORANGE,
        )
        self.lbl_rate.grid(row=0, column=2, sticky="e")

        self.prog_bar = ctk.CTkProgressBar(
            inner, height=10, corner_radius=5,
            progress_color=ORANGE, fg_color=("#e2e8f0", NAVY_LIGHT),
        )
        self.prog_bar.set(0)
        self.prog_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        # ── Overdue Quick Panel ─────────────────────────────────────────
        self.overdue_panel = ctk.CTkFrame(
            self, fg_color=(CARD_LIGHT, CARD_DARK),
            corner_radius=14, border_width=1,
            border_color=("#e2e8f0", NAVY_LIGHT),
        )
        self.overdue_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        od_header = ctk.CTkFrame(self.overdue_panel, fg_color="transparent")
        od_header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            od_header, text="\uE7BA  Overdue Students",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
            text_color=("#ef4444", "#f87171"),
        ).pack(side="left")
        ctk.CTkFrame(self.overdue_panel, height=1,
                     fg_color=("#e2e8f0", NAVY_LIGHT)).pack(fill="x", padx=20, pady=(0, 8))

        self.overdue_scroll = ctk.CTkScrollableFrame(
            self.overdue_panel, fg_color="transparent",
        )
        self.overdue_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.lbl_no_overdue = ctk.CTkLabel(
            self.overdue_scroll,
            text="✅  All students are up-to-date!",
            font=ctk.CTkFont(size=13), text_color="#10b981",
        )
        self.lbl_no_overdue.pack(pady=20)

    def _make_card(self, parent, cfg: dict):
        card = ctk.CTkFrame(
            parent,
            fg_color=(CARD_LIGHT, CARD_DARK),
            corner_radius=14,
            border_width=0,
            height=130,
        )
        card.grid_propagate(False)

        # Clickable overdue card
        if cfg["key"] == "total_overdue":
            card.configure(cursor="hand2")

        # Top-colored stripe
        stripe = ctk.CTkFrame(card, width=5, corner_radius=3, fg_color=cfg["color"])
        stripe.pack(side="left", fill="y", pady=18, padx=(12, 0))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        # Icon
        ctk.CTkLabel(
            content, text=cfg["icon"],
            font=ctk.CTkFont(family="Segoe Fluent Icons", size=36),
            text_color=cfg["color"],
        ).pack(anchor="w")

        # Value
        val_lbl = ctk.CTkLabel(
            content, text="—",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=26, weight="bold"),
            text_color=(("#0f172a"), "white"),
            anchor="w",
        )
        val_lbl.pack(anchor="w")

        # Title + suffix
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.pack(anchor="w", fill="x")
        ctk.CTkLabel(
            bottom, text=cfg["title"],
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=11, weight="bold"),
            text_color=("#64748b", "#94a3b8"), anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            bottom, text=f" · {cfg['suffix']}",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=11),
            text_color=("#94a3b8", "#64748b"), anchor="w",
        ).pack(side="left")

        return card, val_lbl

    # ─────────────────────────────────────────────────────────── Data ── #

    def refresh(self):
        try:
            stats = self.db.get_dashboard_stats()
            self._stats = stats
        except Exception as e:
            print(f"[Dashboard] Error: {e}")
            return

        # Animate value counters
        for cfg, lbl in self._val_labels:
            val = stats.get(cfg["key"], 0)
            self._animate_counter(lbl, val, cfg["fmt"])

        # Progress bar
        collected = float(stats.get("total_collected", 0))
        total     = collected + float(stats.get("total_pending", 0))
        rate      = (collected / total * 100) if total > 0 else 0
        self.prog_bar.set(min(rate / 100, 1.0))
        self.lbl_rate.configure(text=f"{rate:.1f}%")

        # Overdue panel
        self._render_overdue(stats.get("overdue_details", []))

    def _animate_counter(self, label, target_val, fmt, step=0, total_steps=12):
        """Smooth roll-up animation for numeric display."""
        try:
            frac = step / total_steps
            # ease-out curve
            current = target_val * (1 - (1 - frac) ** 3)
            label.configure(text=fmt(current))
            if step < total_steps:
                label.after(25, lambda: self._animate_counter(
                    label, target_val, fmt, step + 1, total_steps))
            else:
                label.configure(text=fmt(target_val))
        except Exception:
            label.configure(text=fmt(target_val))

    def _render_overdue(self, details: list):
        for w in self.overdue_scroll.winfo_children():
            w.destroy()

        if not details:
            ctk.CTkLabel(
                self.overdue_scroll,
                text="✅  All students are up-to-date! No overdue payments.",
                font=ctk.CTkFont(size=13), text_color="#10b981",
            ).pack(pady=20)
            return

        # Column header
        hdr = ctk.CTkFrame(self.overdue_scroll,
                           fg_color=("#f8fafc", NAVY), corner_radius=8)
        hdr.pack(fill="x", pady=(0, 4))
        for txt, w in [("ID", 60), ("Student Name", 0), ("Months Overdue", 130), ("Amount Due", 130)]:
            ctk.CTkLabel(
                hdr, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#64748b", "#94a3b8"), anchor="w",
            ).pack(side="left", padx=10, pady=8)

        for d in details:
            row = ctk.CTkFrame(
                self.overdue_scroll,
                fg_color=("#fff5f5", "#450a0a"),
                corner_radius=8, border_width=1,
                border_color=("#fca5a5", "#7f1d1d"),
            )
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=f"#{d['id']:03d}", width=60,
                         font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8"),
                         anchor="w").pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(row, text=d["name"],
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=("#0f172a", "white"), anchor="w").pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(row, text=f"{d['months']} month{'s' if d['months'] != 1 else ''}",
                         width=130, font=ctk.CTkFont(size=12),
                         text_color=("#dc2626", "#f87171"), anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"₹{d['amount']:,.0f}",
                         width=130, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#ef4444", anchor="e").pack(side="right", padx=14)
