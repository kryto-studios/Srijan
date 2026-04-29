"""
utils/receipt_generator.py
--------------------------
Generates a professional PDF payment receipt using reportlab.
Falls back to a plain-text receipt if reportlab is not installed.
"""

import os
import datetime

RECEIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "receipts")
INSTITUTION  = "SRIJAN ACADEMY"
SUBTITLE     = "Student Fee Management System"


def _ensure_dir():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)


def generate(student: dict, payment: dict) -> str:
    """
    Generate a PDF receipt and return the file path.

    student dict keys: id, name, father_name, course, total_course_fee, total_paid, balance
    payment dict keys: p_id, amount_paid, payment_date, month_name
    """
    _ensure_dir()
    try:
        return _generate_pdf(student, payment)
    except ImportError:
        return _generate_txt(student, payment)


# ──────────────────────────────────────────────────────────────────────────────
#  PDF Generation (reportlab)
# ──────────────────────────────────────────────────────────────────────────────

def _generate_pdf(student: dict, payment: dict) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    receipt_no = f"R-{payment['p_id']:05d}"
    fname      = f"Receipt_{receipt_no}_{student['id']}.pdf"
    fpath      = os.path.join(RECEIPTS_DIR, fname)

    doc  = SimpleDocTemplate(fpath, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    # ── Custom styles ──────────────────────────────────────────────────────
    INDIGO = colors.HexColor("#4f46e5")
    DARK   = colors.HexColor("#0f172a")
    MUTED  = colors.HexColor("#64748b")
    GREEN  = colors.HexColor("#059669")
    RED    = colors.HexColor("#dc2626")

    h1 = ParagraphStyle("h1", fontSize=22, fontName="Helvetica-Bold",
                         textColor=INDIGO, alignment=TA_CENTER, spaceAfter=2)
    h2 = ParagraphStyle("h2", fontSize=11, fontName="Helvetica",
                         textColor=MUTED, alignment=TA_CENTER, spaceAfter=4)
    h3 = ParagraphStyle("h3", fontSize=13, fontName="Helvetica-Bold",
                         textColor=DARK,  spaceAfter=6, spaceBefore=12)
    body = ParagraphStyle("body", fontSize=10, fontName="Helvetica",
                          textColor=DARK, leading=16)
    right = ParagraphStyle("right", fontSize=10, fontName="Helvetica",
                           textColor=MUTED, alignment=TA_RIGHT)

    # ── Build content ──────────────────────────────────────────────────────
    story = []

    # Header
    story.append(Paragraph(f"📚 {INSTITUTION}", h1))
    story.append(Paragraph(SUBTITLE, h2))
    story.append(HRFlowable(width="100%", thickness=2, color=INDIGO, spaceAfter=8))

    # Receipt meta
    story.append(Paragraph("<b>PAYMENT RECEIPT</b>",
                           ParagraphStyle("rc", fontSize=16, fontName="Helvetica-Bold",
                                          textColor=DARK, alignment=TA_CENTER, spaceAfter=4)))
    meta_data = [
        [Paragraph(f"<b>Receipt No:</b> {receipt_no}", body),
         Paragraph(f"<b>Date:</b> {datetime.date.today().strftime('%d-%m-%Y')}", right)],
    ]
    meta_table = Table(meta_data, colWidths=["50%", "50%"])
    meta_table.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"),
                            spaceAfter=10, spaceBefore=6))

    # Student info
    story.append(Paragraph("STUDENT INFORMATION", h3))
    info_data = [
        ["Student ID",  f"#{student['id']:04d}"],
        ["Name",        student["name"]],
        ["Father Name", student["father_name"]],
        ["Course",      student["course"]],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR",     (0,0), (0,-1), MUTED),
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ]))
    story.append(info_table)

    # Payment details
    story.append(Paragraph("PAYMENT DETAILS", h3))
    amt  = float(payment["amount_paid"])
    pdate = str(payment["payment_date"])
    pay_data = [
        ["Month",         payment["month_name"]],
        ["Payment Date",  pdate],
        ["Amount Paid",   f"INR {amt:,.2f}"],
    ]
    pay_table = Table(pay_data, colWidths=[4*cm, 12*cm])
    pay_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR",     (0,0), (0,-1), MUTED),
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        # Highlight amount row
        ("BACKGROUND",    (1,2), (1,2), colors.HexColor("#ecfdf5")),
        ("TEXTCOLOR",     (1,2), (1,2), GREEN),
        ("FONTNAME",      (1,2), (1,2), "Helvetica-Bold"),
        ("FONTSIZE",      (1,2), (1,2), 12),
    ]))
    story.append(pay_table)

    # Fee summary
    story.append(Paragraph("FEE SUMMARY", h3))
    total_fee = float(student["total_course_fee"])
    total_paid = float(student["total_paid"])
    balance   = float(student["balance"])
    sum_data = [
        ["Total Course Fee",     f"INR {total_fee:,.2f}"],
        ["Total Paid Till Date", f"INR {total_paid:,.2f}"],
        ["Remaining Balance",    f"INR {balance:,.2f}" if balance > 0 else "FULLY CLEARED"],
    ]
    sum_table = Table(sum_data, colWidths=[6*cm, 10*cm])
    bal_color = colors.HexColor("#450a0a") if balance > 0 else colors.HexColor("#064e3b")
    bal_text  = RED if balance > 0 else GREEN
    sum_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR",     (0,0), (0,-1), MUTED),
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("BACKGROUND",    (1,2), (1,2), bal_color),
        ("TEXTCOLOR",     (1,2), (1,2), bal_text),
        ("FONTNAME",      (1,2), (1,2), "Helvetica-Bold"),
        ("FONTSIZE",      (1,2), (1,2), 12),
    ]))
    story.append(sum_table)

    # Signatures
    story.append(Spacer(1, 1.5*cm))
    sig_data = [
        [Paragraph("________________________", body),
         Paragraph("________________________", body)],
        [Paragraph("Student Signature", ParagraphStyle("sig", fontSize=9,
                   fontName="Helvetica", textColor=MUTED, alignment=TA_CENTER)),
         Paragraph("Authorized Signature", ParagraphStyle("sig2", fontSize=9,
                   fontName="Helvetica", textColor=MUTED, alignment=TA_CENTER))],
    ]
    sig_table = Table(sig_data, colWidths=["50%", "50%"])
    sig_table.setStyle(TableStyle([
        ("ALIGN",  (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(sig_table)

    # Footer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"),
                            spaceAfter=6))
    story.append(Paragraph(
        "This is a computer-generated receipt and does not require a physical signature.",
        ParagraphStyle("footer", fontSize=8, fontName="Helvetica",
                       textColor=MUTED, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f"Generated on {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | {INSTITUTION}",
        ParagraphStyle("footer2", fontSize=8, fontName="Helvetica",
                       textColor=MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    return fpath


# ──────────────────────────────────────────────────────────────────────────────
#  Plain-text Fallback
# ──────────────────────────────────────────────────────────────────────────────

def _generate_txt(student: dict, payment: dict) -> str:
    receipt_no = f"R-{payment['p_id']:05d}"
    fname      = f"Receipt_{receipt_no}_{student['id']}.txt"
    fpath      = os.path.join(RECEIPTS_DIR, fname)

    lines = [
        "=" * 50,
        f"  {INSTITUTION}",
        f"  {SUBTITLE}",
        "=" * 50,
        f"  PAYMENT RECEIPT",
        f"  Receipt No : {receipt_no}",
        f"  Date       : {datetime.date.today().strftime('%d-%m-%Y')}",
        "-" * 50,
        "  STUDENT INFORMATION",
        f"  ID     : #{student['id']:04d}",
        f"  Name   : {student['name']}",
        f"  Father : {student['father_name']}",
        f"  Course : {student['course']}",
        "-" * 50,
        "  PAYMENT DETAILS",
        f"  Month  : {payment['month_name']}",
        f"  Date   : {payment['payment_date']}",
        f"  Amount : INR {float(payment['amount_paid']):,.2f}",
        "-" * 50,
        "  FEE SUMMARY",
        f"  Total Fee  : INR {float(student['total_course_fee']):,.2f}",
        f"  Total Paid : INR {float(student['total_paid']):,.2f}",
        f"  Balance    : INR {float(student['balance']):,.2f}",
        "=" * 50,
        "  Computer generated receipt.",
        "=" * 50,
    ]

    with open(fpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return fpath


def open_receipt(fpath: str):
    """Open the receipt file with the default system application."""
    try:
        os.startfile(fpath)
    except AttributeError:
        import subprocess
        subprocess.Popen(["xdg-open", fpath])
    except Exception as e:
        print(f"[Receipt] Could not open file: {e}")
