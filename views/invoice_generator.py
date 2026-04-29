"""
views/invoice_generator.py
--------------------------
UI View to generate and download professional invoices.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date, timedelta
from tkcalendar import DateEntry
import urllib.parse
import webbrowser
import threading
import time

from utils import invoice_pdf_generator

# Palette
ORANGE     = "#c2410c"
ORANGE_HOV = "#9a3412"
NAVY       = "#0f172a"
NAVY_LIGHT = "#1e293b"


class InvoiceGeneratorView(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = db
        self._selected_student = None
        self._search_results = []
        self._is_selecting = False
        self._last_saved_pdf = None
        self._build_ui()

    def _build_ui(self):
        # ── HEADER ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        title_f = ctk.CTkFrame(header, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(
            title_f, text="Invoice Generator",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_f, text="Create and download professional PDF invoices",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=12),
            text_color="#64748b",
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=2, fg_color=("#e2e8f0", NAVY_LIGHT)).pack(
            fill="x", padx=30, pady=(0, 20)
        )

        # ── SCROLLABLE BODY ──
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30)

        card = ctk.CTkFrame(
            scroll, fg_color=("#ffffff", NAVY_LIGHT), corner_radius=16,
            border_width=1, border_color=("#e2e8f0", "#334155"),
        )
        card.pack(fill="x", pady=5)
        inn = ctk.CTkFrame(card, fg_color="transparent")
        inn.pack(fill="both", expand=True, padx=30, pady=25)

        # ── 1. SELECT STUDENT ──
        self._section(inn, "\uE71C  Select Student")
        
        search_container = ctk.CTkFrame(inn, fg_color="transparent")
        search_container.pack(fill="x", pady=5)
        
        self.var_search = ctk.StringVar()
        self.var_search.trace_add("write", self._on_search_type)
        
        self.ent_search = ctk.CTkEntry(
            search_container, textvariable=self.var_search,
            placeholder_text="Start typing student name or ID...",
            height=42, corner_radius=8,
            border_width=1, border_color=("#e2e8f0", "#334155"),
            font=ctk.CTkFont(size=14)
        )
        self.ent_search.pack(fill="x")

        # Suggestion Box (Hidden initially)
        self.suggest_frame = ctk.CTkScrollableFrame(
            search_container, fg_color=("#f1f5f9", "#0f172a"),
            border_width=1, border_color=("#e2e8f0", "#334155"),
            height=140, corner_radius=8
        )

        # ── 2. INVOICE DETAILS ──
        self._section(inn, "\uE8A5  Invoice Details")
        
        r1 = self._row(inn)
        self.ent_inv_no = self._entry(r1, 0, "Invoice Number *", "e.g. SI/INV/2026/001")
        self.ent_inv_no.insert(0, f"SI/INV/{date.today().year}/001")
        
        self.var_mode = ctk.StringVar(value="Online")
        self._dropdown(r1, 1, "Payment Mode", ["Pending", "Cash", "Online", "Cheque", "UPI"], self.var_mode)

        r2 = self._row(inn)
        self.de_date = self._date_picker(r2, 0, "Invoice Date *")
        self.de_due  = self._date_picker(r2, 1, "Due Date *")
        self.de_due.set_date(date.today() + timedelta(days=7))
        
        # ── 2B. EDITABLE STUDENT DETAILS ──
        self._section(inn, "\uE77B  Editable Student Details")
        
        r_ed1 = self._row(inn)
        self.ent_phone = self._entry(r_ed1, 0, "Student Phone", "e.g. 9876543210")
        
        # Address needs a bit more space, we'll use an entry for simplicity instead of textbox
        self.ent_address = self._entry(r_ed1, 1, "Student Address", "e.g. 123 Main St")

        # ── 3. FEE CALCULATION ──
        self._section(inn, "\uE825  Fee Calculations")
        
        r3 = self._row(inn)
        from utils.fee_calculator import FREQUENCIES
        self.var_freq = ctk.StringVar(value="Monthly")
        self._dropdown(r3, 0, "Fee Frequency", FREQUENCIES, self.var_freq)
        self.ent_base = self._entry(r3, 1, "Base Amount (₹) *", "0")
        
        r4 = self._row(inn)
        self.ent_disc = self._entry(r4, 0, "Discount (₹)", "0")
        self.ent_gst = self._entry(r4, 1, "GST (%)", "18")
        
        r5 = self._row(inn)
        self.ent_paid = self._entry(r5, 0, "Amount Paid (₹) *", "0")
        self.ent_due  = self._entry(r5, 1, "Amount Due (₹)", "0")
        
        # Bind key releases to auto-calculate due amount
        for e in (self.ent_base, self.ent_disc, self.ent_gst, self.ent_paid):
            e.bind("<KeyRelease>", self._calculate_due)
        
        # ── 4. ACTIONS ──
        bf = ctk.CTkFrame(inn, fg_color="transparent")
        bf.pack(fill="x", pady=(30, 0))
        
        ctk.CTkButton(
            bf, text="\uE8A5  Generate & Download Invoice", height=46, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            fg_color=ORANGE, hover_color=ORANGE_HOV,
            command=self._generate,
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            bf, text="💬 Send to WhatsApp", height=46, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
            fg_color="#10b981", hover_color="#059669", # Green
            command=self._send_whatsapp,
        ).pack(side="left", padx=(0, 10))
        
        self.lbl_status = ctk.CTkLabel(bf, text="", font=ctk.CTkFont(size=13), text_color="#059669")
        self.lbl_status.pack(side="left", padx=10)

    # ── Helpers ──

    def _section(self, p, text):
        f = ctk.CTkFrame(p, fg_color="transparent")
        f.pack(fill="x", pady=(25, 6))
        ctk.CTkLabel(
            f, text=text,
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
            text_color=(ORANGE, "#fb923c"), anchor="w",
        ).pack(side="left")
        ctk.CTkFrame(p, height=1, fg_color=("#e2e8f0", "#27272a")).pack(fill="x", pady=(0, 10))

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

    def _dropdown(self, row, col, label, values, var):
        f = ctk.CTkFrame(row, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=(0, 8) if col == 0 else (8, 0))
        self._label(f, label)
        ctk.CTkOptionMenu(
            f, values=values, variable=var, height=42, corner_radius=8,
            fg_color=("#f8fafc", NAVY),
            button_color=ORANGE, button_hover_color=ORANGE_HOV,
        ).pack(fill="x")

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

    # ── Logic ──

    def _on_search_type(self, *args):
        if self._is_selecting:
            return
            
        query = self.var_search.get().strip()
        if not query:
            self.suggest_frame.pack_forget()
            return
            
        try:
            results = self.db.search_students(query)
            
            # Clear old suggestions
            for child in self.suggest_frame.winfo_children():
                child.destroy()
                
            if not results:
                self.suggest_frame.pack_forget()
                return
                
            self.suggest_frame.pack(fill="x", pady=(2, 0))
            self._search_results = results
            
            for s in results[:10]: # Show top 10 suggestions
                btn_text = f"#{s['id']:03d} - {s['name']} (Course: {s['course']})"
                btn = ctk.CTkButton(
                    self.suggest_frame, text=btn_text, anchor="w",
                    font=ctk.CTkFont(size=13),
                    fg_color="transparent", text_color=("#0f172a", "#f8fafc"),
                    hover_color=("#e2e8f0", "#1e293b"), height=32, corner_radius=6,
                    command=lambda sid=s['id']: self._select_suggestion(sid)
                )
                btn.pack(fill="x", padx=2, pady=1)
                
        except Exception as e:
            pass

    def _select_suggestion(self, sid):
        try:
            student = next(s for s in self._search_results if s['id'] == sid)
            self._selected_student = student
            
            self._is_selecting = True
            self.var_search.set(f"#{student['id']:03d} - {student['name']}")
            self._is_selecting = False
            
            self.suggest_frame.pack_forget()
            
            # Autofill Fee Details
            self.ent_base.delete(0, "end")
            self.ent_base.insert(0, str(student.get("total_course_fee", 0)))
            self.ent_disc.delete(0, "end")
            self.ent_disc.insert(0, "0")
            
            # Autofill Phone and Address
            self.ent_phone.delete(0, "end")
            self.ent_phone.insert(0, student.get("phone") or "")
            self.ent_address.delete(0, "end")
            self.ent_address.insert(0, student.get("address") or "")
            
            # Autofill Frequency
            self.var_freq.set(student.get("fee_frequency", "Monthly"))
            
            self._calculate_due()
            
        except Exception as e:
            print("Selection error:", e)

    def _calculate_due(self, *_):
        if self._is_selecting:
            return
        try:
            base_amt = float(self.ent_base.get().strip() or 0)
            discount = float(self.ent_disc.get().strip() or 0)
            gst_pct  = float(self.ent_gst.get().strip() or 0)
            amt_paid = float(self.ent_paid.get().strip() or 0)
            
            subtotal = base_amt - discount
            tax      = (subtotal * gst_pct) / 100.0
            total    = subtotal + tax
            
            due      = total - amt_paid
            
            # Update due field
            self.ent_due.delete(0, "end")
            self.ent_due.insert(0, f"{max(0.0, due):.2f}")
        except ValueError:
            pass

    def _generate(self):
        if not self._selected_student:
            messagebox.showwarning("Warning", "Please search and select a student first.")
            return
            
        inv_no = self.ent_inv_no.get().strip()
        if not inv_no:
            messagebox.showwarning("Warning", "Invoice Number is required.")
            return
            
        try:
            base_amt = float(self.ent_base.get().strip() or 0)
            discount = float(self.ent_disc.get().strip() or 0)
            gst_pct  = float(self.ent_gst.get().strip() or 0)
            amt_paid = float(self.ent_paid.get().strip() or 0)
            amt_due  = float(self.ent_due.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Error", "All fee amounts must be valid numbers.")
            return

        inv_date = str(self.de_date.get_date())
        due_date = str(self.de_due.get_date())
        mode     = self.var_mode.get()
        
        # Fetch the editable fields from UI instead of selected_student
        address_edited = self.ent_address.get().strip()
        phone_edited   = self.ent_phone.get().strip()
        freq_edited    = self.var_freq.get()
        
        # Prepare Data Dict for the PDF Generator
        data = {
            "student_id": self._selected_student["id"],
            "student_name": self._selected_student["name"],
            "address": address_edited if address_edited else self._selected_student.get("address", "N/A"),
            "course": self._selected_student["course"],
            "subjects": self._selected_student.get("subjects", "N/A"),
            "phone": phone_edited if phone_edited else self._selected_student.get("phone", "N/A"),
            "fee_frequency": freq_edited,
            "email": "N/A",
            
            "invoice_no": inv_no,
            "invoice_date": inv_date,
            "due_date": due_date,
            "received_mode": mode,
            
            "base_amount": base_amt,
            "discount": discount,
            "gst_pct": gst_pct,
            "amount_paid": amt_paid,
            "amount_due": amt_due,
        }
        
        # Ask User for Save Location
        safe_inv_no = inv_no.replace('/', '-').replace('\\', '-')
        default_filename = f"Invoice_{safe_inv_no}_{self._selected_student['id']}.pdf"
        
        save_path = filedialog.asksaveasfilename(
            title="Save Invoice PDF",
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )
        
        if not save_path:
            return # User cancelled the save dialog
        
        try:
            fpath = invoice_pdf_generator.generate_invoice(data, save_path=save_path)
            self._last_saved_pdf = fpath
            data["save_path"] = fpath # Include the final saved path
            self.db.save_invoice_record(data) # Log the invoice permanently
            self.lbl_status.configure(text=f"✔ Invoice Saved & Logged successfully!")
            invoice_pdf_generator.open_invoice(fpath)
        except Exception as e:
            messagebox.showerror("PDF Generation Error", str(e))

    def _send_whatsapp(self):
        if not self._selected_student:
            messagebox.showwarning("Warning", "Please select a student first.")
            return
            
        phone = self.ent_phone.get().strip()
        if not phone:
            messagebox.showwarning("Warning", "No phone number provided for this student.")
            return
            
        # Clean up phone number
        clean_phone = "".join(c for c in phone if c.isdigit() or c == "+")
        if not clean_phone.startswith("+"):
            if len(clean_phone) == 10:
                clean_phone = "+91" + clean_phone # Assume India
            else:
                clean_phone = "+" + clean_phone # Attempt directly
                
        name = self._selected_student["name"]
        inv_no = self.ent_inv_no.get().strip()
        amt_due = self.ent_due.get().strip()
        
        message = (
            f"Hello {name},\n\n"
            f"Welcome to Srijan Institute!\n"
            f"Your invoice has been generated successfully.\n\n"
            f"Invoice No: {inv_no}\n"
            f"Amount Due: ₹{amt_due}\n\n"
            f"Please find the invoice document attached.\n\n"
            f"Thank you!"
        )
        
        encoded_msg = urllib.parse.quote(message)
        url = f"https://wa.me/{clean_phone.replace('+', '')}?text={encoded_msg}"
        
        # Copy the PDF file to the Windows Clipboard using PowerShell
        if self._last_saved_pdf:
            try:
                import subprocess
                # This copies the actual file to clipboard, so Ctrl+V pastes it as an attachment
                subprocess.run(["powershell", "-command", f"Set-Clipboard -Path '{self._last_saved_pdf}'"], check=False)
            except Exception as e:
                print("Could not copy to clipboard:", e)
        
        try:
            webbrowser.open(url)
            self.lbl_status.configure(text=f"✔ WhatsApp opening. Auto-pasting in 5 seconds...")
            
            # Start a background thread to auto-paste
            def auto_paste():
                time.sleep(6) # Wait 6 seconds for WhatsApp Web/App to fully load
                try:
                    import subprocess
                    subprocess.run([
                        "powershell", "-command", 
                        "$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('^v')"
                    ], check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception as e:
                    print("Auto-paste failed:", e)
                    
            if self._last_saved_pdf:
                threading.Thread(target=auto_paste, daemon=True).start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {e}")
