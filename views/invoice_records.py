"""
views/invoice_records.py
------------------------
Displays all generated invoices and allows searching/filtering.
"""

import customtkinter as ctk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
from utils import invoice_pdf_generator
import shutil

ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"

class InvoiceRecordsView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._build_ui()
        
    def _build_ui(self):
        # ── HEADER ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Invoice Records",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="View, search, and open past generated invoices",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(fill="x", padx=30, pady=(0, 20))

        # ── TOOLBAR ──
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=30, pady=(0, 15))

        # Search Bar
        self.var_search = ctk.StringVar()
        ctk.CTkEntry(
            toolbar, textvariable=self.var_search,
            placeholder_text="Search by Name, Invoice No, or ID...",
            height=42, width=300, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#334155"),
            font=ctk.CTkFont(size=14)
        ).pack(side="left")

        ctk.CTkButton(
            toolbar, text="\uE721 Search", height=42, corner_radius=8,
            font=ctk.CTkFont(weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self.refresh,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            toolbar, text="Refresh", height=42, corner_radius=8,
            fg_color=NAVY_LIGHT, hover_color="#334155",
            command=self.refresh,
        ).pack(side="left")

        # ── DATA TABLE ──
        table_frame = ctk.CTkFrame(
            self, fg_color=("#ffffff", NAVY_LIGHT),
            corner_radius=14, border_width=1, border_color=("#e2e8f0", "#334155")
        )
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        # Theme Configuration
        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        
        style.configure(
            "Inv.Treeview",
            background=NAVY_LIGHT, foreground="#e2e8f0",
            rowheight=40, fieldbackground=NAVY_LIGHT, borderwidth=0,
            font=("Segoe UI", 11)
        )
        style.configure(
            "Inv.Treeview.Heading",
            background=NAVY, foreground="#94a3b8",
            relief="flat", font=("Segoe UI", 11, "bold"), padding=(6, 10)
        )
        style.map("Inv.Treeview", background=[("selected", ORANGE)], foreground=[("selected", "white")])

        cols = ("id", "inv_no", "date", "name", "paid", "due", "mode", "action")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Inv.Treeview")

        headers = {
            "id": ("ID", 65, "center"),
            "inv_no": ("Invoice No.", 150, "w"),
            "date": ("Date", 120, "center"),
            "name": ("Student Name", 200, "w"),
            "paid": ("Amount Paid", 110, "e"),
            "due": ("Amount Due", 110, "e"),
            "mode": ("Payment Mode", 120, "center"),
            "action": ("Action", 120, "center"),
        }
        for col, (text, width, anchor) in headers.items():
            self.tree.heading(col, text=text, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor)

        # Scrollbar
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))
        self.tree.pack(side="top", fill="both", expand=True, pady=10, padx=(10, 0))

        # ── ACTION BAR ──
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=30, pady=(0, 30))
        
        ctk.CTkButton(
            action_bar, text="\uE8A5  Open Selected Invoice (Save/Print)", 
            height=46, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._open_selected,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            action_bar, text="⬇️ Download Copy", 
            height=46, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            fg_color="#3b82f6", hover_color="#2563eb",
            command=self._download_selected,
        ).pack(side="left")

        # Events
        self.tree.bind("<Double-1>", lambda e: self._open_selected())
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        
        # Data
        self._invoices = []
        self.refresh()

    def refresh(self):
        """Fetch invoices and refresh the table."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        query = self.var_search.get().strip()
        try:
            self._invoices = self.db.search_invoices(query)
            for inv in self._invoices:
                self.tree.insert("", "end", iid=inv["id"], values=(
                    f"#{inv['student_id']:03d}",
                    inv["invoice_no"],
                    inv["invoice_date"],
                    inv["student_name"],
                    f"₹{inv['amount_paid']:,.2f}",
                    f"₹{inv['amount_due']:,.2f}",
                    inv["payment_mode"],
                    "⬇️ Download"
                ))
        except Exception as e:
            print(f"Error loading invoices: {e}")

    def _on_tree_click(self, event):
        """Handle clicks on the action column to trigger download."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#8":  # The 'action' column
                item_id = self.tree.identify_row(event.y)
                if item_id:
                    self.tree.selection_set(item_id)
                    self._download_selected()

    def _open_selected(self):
        """Open the PDF when the button is clicked or row is double-clicked."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Invoice", "Please select an invoice from the list first.")
            return
            
        inv_id = int(selected[0])
        invoice = next((i for i in self._invoices if i["id"] == inv_id), None)
        
        if invoice and invoice.get("file_path"):
            try:
                invoice_pdf_generator.open_invoice(invoice["file_path"])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open invoice file.\nIt may have been moved or deleted.\n\nError: {e}")
        else:
            messagebox.showwarning("Not Found", "File path for this invoice is missing.")

    def _download_selected(self):
        """Download (copy) the selected PDF to a new location."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Invoice", "Please select an invoice from the list first.")
            return
            
        inv_id = int(selected[0])
        invoice = next((i for i in self._invoices if i["id"] == inv_id), None)
        
        if not invoice or not invoice.get("file_path"):
            messagebox.showwarning("Not Found", "File path for this invoice is missing.")
            return
            
        source_path = invoice["file_path"]
        
        # Suggest a default filename based on the invoice number
        safe_inv = invoice["invoice_no"].replace('/', '-').replace('\\', '-')
        default_name = f"{safe_inv}_{invoice['student_name'].replace(' ', '_')}.pdf"
        
        dest_path = filedialog.asksaveasfilename(
            title="Download Invoice PDF",
            initialfile=default_name,
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )
        
        if dest_path:
            try:
                shutil.copy(source_path, dest_path)
                messagebox.showinfo("Success", f"Invoice successfully downloaded to:\n{dest_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download the invoice.\n\nError: {e}")
