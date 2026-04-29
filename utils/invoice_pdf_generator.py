"""
utils/invoice_pdf_generator.py
------------------------------
Generates a highly professional, modern PDF invoice.
Custom layout for Srijan Institute.
"""

import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

INVOICES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "invoices")

def _ensure_dir():
    os.makedirs(INVOICES_DIR, exist_ok=True)

def generate_invoice(invoice_data: dict, save_path: str = None) -> str:
    """
    Generate a modern, clean PDF invoice.
    invoice_data should contain:
      - student_name, student_id, course, address, phone, email
      - invoice_no, invoice_date, due_date
      - base_amount, discount, gst_pct
      - amount_paid, amount_due
      - received_mode (Cash/Online/Cheque/UPI)
    """
    if not save_path:
        _ensure_dir()
        safe_inv_no = invoice_data.get('invoice_no', '001').replace('/', '-').replace('\\', '-')
        fname = f"Invoice_{safe_inv_no}_{invoice_data.get('student_id', '0')}.pdf"
        save_path = os.path.join(INVOICES_DIR, fname)

    doc = SimpleDocTemplate(save_path, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()

    # -- Modern Color Palette --
    NAVY       = colors.HexColor("#1e293b")
    PRIMARY    = colors.HexColor("#ea580c")  # Professional Orange
    TEXT_DARK  = colors.HexColor("#334155")
    TEXT_MUTED = colors.HexColor("#64748b")
    BG_LIGHT   = colors.HexColor("#f8fafc")
    BORDER     = colors.HexColor("#e2e8f0")

    # -- Typography Styles --
    title_st = ParagraphStyle("title", fontSize=28, fontName="Helvetica-Bold", textColor=NAVY, alignment=TA_RIGHT)
    inst_name = ParagraphStyle("inst", fontSize=20, fontName="Helvetica-Bold", textColor=NAVY)
    inst_tag  = ParagraphStyle("tag", fontSize=10, fontName="Helvetica", textColor=PRIMARY)
    
    lbl_st = ParagraphStyle("lbl", fontSize=9, fontName="Helvetica-Bold", textColor=TEXT_MUTED, spaceAfter=2)
    val_st = ParagraphStyle("val", fontSize=10, fontName="Helvetica", textColor=TEXT_DARK, spaceAfter=8)
    val_bold = ParagraphStyle("valb", fontSize=10, fontName="Helvetica-Bold", textColor=TEXT_DARK, spaceAfter=8)
    
    th_st = ParagraphStyle("th", fontSize=10, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_CENTER)
    tc_st = ParagraphStyle("tc", fontSize=10, fontName="Helvetica", textColor=TEXT_DARK, alignment=TA_CENTER)
    td_st = ParagraphStyle("td", fontSize=10, fontName="Helvetica", textColor=TEXT_DARK, alignment=TA_LEFT)
    
    story = []

    # -------------------------------------------------------------------------
    # 1. HEADER (Logo Left, INVOICE title Right)
    # -------------------------------------------------------------------------
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
    inst_block = []
    if os.path.exists(logo_path):
        img = Image(logo_path, width=4*cm, height=4*cm, kind='proportional')
        img.hAlign = 'LEFT'
        inst_block.append(img)
    else:
        inst_block.append(Paragraph("SRIJAN INSTITUTE", inst_name))
        inst_block.append(Paragraph("LEARN • GROW • SUCCEED", inst_tag))
    
    header_data = [[
        inst_block,
        Paragraph("TAX INVOICE", title_st)
    ]]
    header_table = Table(header_data, colWidths=[9*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=15))

    # -------------------------------------------------------------------------
    # 2. INSTITUTE INFO & INVOICE DETAILS
    # -------------------------------------------------------------------------
    inst_info = [
        Paragraph("Banaras Rd, near jayka hotel, Cseb chowk", val_st),
        Paragraph("Ambikapur, Chhattisgarh 497001", val_st),
        Paragraph("Phone: 098898 07321", val_st),
    ]
    
    inv_info = [
        [Paragraph("Invoice No:", lbl_st), Paragraph(invoice_data.get('invoice_no', '-'), val_bold)],
        [Paragraph("Invoice Date:", lbl_st), Paragraph(invoice_data.get('invoice_date', '-'), val_st)],
        [Paragraph("Due Date:", lbl_st), Paragraph(invoice_data.get('due_date', '-'), val_st)],
    ]
    inv_table = Table(inv_info, colWidths=[3*cm, 5*cm])
    inv_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    top_meta_data = [[inst_info, inv_table]]
    top_meta_table = Table(top_meta_data, colWidths=[10*cm, 8*cm])
    top_meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(top_meta_table)
    story.append(Spacer(1, 1*cm))

    # -------------------------------------------------------------------------
    # 3. BILL TO SECTION
    # -------------------------------------------------------------------------
    def _make_block(title, lines):
        block = [Paragraph(title, ParagraphStyle("bhdr", fontSize=11, fontName="Helvetica-Bold", textColor=NAVY, spaceAfter=6)),
                 HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8)]
        for L in lines:
            block.append(Paragraph(L, val_st))
        return block

    bill_to_lines = [
        f"<b>{invoice_data.get('student_name', '')}</b>",
        f"Student ID: #{invoice_data.get('student_id', 0):04d}",
        f"Course: {invoice_data.get('course', '')}",
        f"Address: {invoice_data.get('address', 'N/A')}",
        f"Phone: {invoice_data.get('phone', 'N/A')}",
    ]
    
    subjects = invoice_data.get('subjects')
    if subjects and subjects != "N/A":
        bill_to_lines.insert(3, f"Subjects: {subjects}")
    
    # We span "Bill To" across 12cm, leaving right empty
    bill_table = Table([[_make_block("BILL TO", bill_to_lines), ""]], colWidths=[9*cm, 9*cm])
    story.append(bill_table)
    story.append(Spacer(1, 0.8*cm))

    # -------------------------------------------------------------------------
    # 4. ITEMIZED TABLE
    # -------------------------------------------------------------------------
    base_amt = float(invoice_data.get('base_amount', 0))
    fee_freq = invoice_data.get('fee_frequency', 'Monthly')
    table_data = [
        [Paragraph("DESCRIPTION", th_st), Paragraph("QTY", th_st), 
         Paragraph("RATE (₹)", th_st), Paragraph("AMOUNT (₹)", th_st)],
        
        [Paragraph(f"Course Fee ({fee_freq}) - {invoice_data.get('course', '')}", td_st),
         Paragraph("1", tc_st), Paragraph(f"{base_amt:,.2f}", tc_st), Paragraph(f"{base_amt:,.2f}", tc_st)]
    ]
    
    # Empty space row to make it look spacious
    table_data.append(["", "", "", ""])

    item_table = Table(table_data, colWidths=[9.5*cm, 2*cm, 3.25*cm, 3.25*cm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,1), (-1,-1), 1, BORDER),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 0.5*cm))

    # -------------------------------------------------------------------------
    # 5. SUMMARY & TOTALS
    # -------------------------------------------------------------------------
    discount = float(invoice_data.get('discount', 0))
    gst_pct  = float(invoice_data.get('gst_pct', 18))
    
    subtotal = base_amt - discount
    tax      = (subtotal * gst_pct) / 100
    total    = subtotal + tax
    
    paid     = float(invoice_data.get('amount_paid', 0))
    due      = float(invoice_data.get('amount_due', 0))

    def _tot_row(lbl, val, is_bold=False, is_highlight=False):
        c_lbl = NAVY if is_bold else TEXT_MUTED
        c_val = PRIMARY if is_highlight else (NAVY if is_bold else TEXT_DARK)
        f_lbl = "Helvetica-Bold" if is_bold else "Helvetica"
        return [
            Paragraph(lbl, ParagraphStyle("tl", fontSize=10, fontName=f_lbl, textColor=c_lbl)),
            Paragraph(f"₹ {val:,.2f}", ParagraphStyle("tv", fontSize=11 if is_bold else 10, fontName="Helvetica-Bold", textColor=c_val, alignment=TA_RIGHT))
        ]

    totals_data = [
        _tot_row("Subtotal", base_amt),
        _tot_row("Discount", discount),
        _tot_row(f"Tax ({gst_pct}% GST)", tax),
        _tot_row("Total Amount", total, is_bold=True),
        _tot_row("Amount Paid", paid),
        _tot_row("AMOUNT DUE", due, is_bold=True, is_highlight=True),
    ]
    
    tot_table = Table(totals_data, colWidths=[4*cm, 3.5*cm])
    tot_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEABOVE', (0,3), (-1,3), 1, BORDER), # Line before Total
        ('LINEABOVE', (0,5), (-1,5), 2, NAVY),   # Line before Amount Due
    ]))

    # Payment Notes
    mode = invoice_data.get('received_mode', 'Pending')
    notes_data = [
        Paragraph("<b>Payment Information:</b>", ParagraphStyle("n1", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY, spaceAfter=4)),
        Paragraph(f"Payment Method: <b>{mode}</b>", val_st),
        Spacer(1, 10),
        Paragraph("<b>Bank Transfer Details:</b>", ParagraphStyle("n1", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY, spaceAfter=4)),
        Paragraph("Bank: HDFC Bank", val_st),
        Paragraph("Account: 5020 1234 5678 90", val_st),
        Paragraph("IFSC: HDFC0001234", val_st),
    ]
    
    bottom_layout = Table([[notes_data, tot_table]], colWidths=[10*cm, 8*cm])
    bottom_layout.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(bottom_layout)
    story.append(Spacer(1, 1.5*cm))

    # -------------------------------------------------------------------------
    # 6. FOOTER
    # -------------------------------------------------------------------------
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=15))
    
    sig_table = Table([[
        Paragraph("Thank you for your business!", ParagraphStyle("ty", fontSize=10, fontName="Helvetica-Oblique", textColor=TEXT_MUTED)),
        Paragraph("Authorized Signatory", ParagraphStyle("sig", fontSize=10, fontName="Helvetica-Bold", textColor=NAVY, alignment=TA_RIGHT))
    ]], colWidths=[9*cm, 9*cm])
    story.append(sig_table)
    
    doc.build(story)
    return save_path

def open_invoice(fpath: str):
    try:
        os.startfile(fpath)
    except AttributeError:
        import subprocess
        subprocess.Popen(["xdg-open", fpath])
    except Exception as e:
        print(f"[Invoice] Could not open file: {e}")
