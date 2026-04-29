"""utils/exporter.py — CSV export utility."""

import csv, os
from datetime import datetime
from tkinter import filedialog, messagebox


def export_students_csv(students: list, parent=None) -> bool:
    """Export students list to a CSV file chosen by the user."""
    fpath = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        initialfile=f"students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        title="Export Students to CSV",
    )
    if not fpath:
        return False

    fieldnames = ["ID", "Member ID", "Name", "Father Name", "DOB", "Gender", "Category", "Course",
                  "Course Type", "Admission Date",
                  "Total Fee", "Total Paid", "Balance", "Status"]
    try:
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in students:
                writer.writerow({
                    "ID":               s.get("id", ""),
                    "Member ID":        s.get("member_id", ""),
                    "Name":             s.get("name", ""),
                    "Father Name":      s.get("father_name", ""),
                    "DOB":              s.get("dob", ""),
                    "Gender":           s.get("gender", ""),
                    "Category":         s.get("category", ""),
                    "Course":           s.get("course", ""),
                    "Course Type":      s.get("course_type", "Annual"),
                    "Admission Date":   s.get("admission_date", ""),
                    "Total Fee":        f"{float(s.get('total_course_fee',0)):,.2f}",
                    "Total Paid":       f"{float(s.get('total_paid',0)):,.2f}",
                    "Balance":          f"{float(s.get('balance',0)):,.2f}",
                    "Status":           s.get("_status", ""),
                })
        messagebox.showinfo("Export Successful", f"Exported to:\n{fpath}", parent=parent)
        return True
    except Exception as e:
        messagebox.showerror("Export Failed", str(e), parent=parent)
        return False
