"""utils/importer.py — CSV import utility."""

import csv
from tkinter import filedialog, messagebox

def import_students_csv(db, parent=None) -> bool:
    """Import students from a CSV file and add them to the database."""
    fpath = filedialog.askopenfilename(
        parent=parent,
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        title="Import Students from CSV"
    )
    if not fpath:
        return False

    success_count = 0
    error_count = 0
    try:
        with open(fpath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            # Require minimum fields
            expected_fields = {"Name", "Course", "Total Fee"}
            if not expected_fields.issubset(set(reader.fieldnames or [])):
                messagebox.showerror(
                    "Invalid Format", 
                    f"CSV must contain at least the following columns:\n{', '.join(expected_fields)}",
                    parent=parent
                )
                return False

            for row in reader:
                try:
                    # Clean and default missing data
                    name = row.get("Name", "").strip()
                    if not name:
                        continue
                        
                    fname = row.get("Father Name", "").strip() or "N/A"
                    dob = row.get("DOB", "").strip() or "2000-01-01"
                    
                    # Normalizer gender
                    raw_gen = row.get("Gender", "").strip().upper()
                    if raw_gen.startswith("M"): gender = "Male"
                    elif raw_gen.startswith("F"): gender = "Female"
                    elif raw_gen.startswith("T"): gender = "Other"
                    else: gender = "Not Specified"
                    
                    category = row.get("Category", "").strip() or "General"
                    course = row.get("Course", "").strip() or "General"
                    c_type = row.get("Course Type", "").strip() or "Annual"
                    adm_date = row.get("Admission Date", "").strip() or None
                    
                    try:
                        total_fee = float(str(row.get("Total Fee", "0")).replace(",", ""))
                    except ValueError:
                        total_fee = 0.0

                    db.add_student(
                        name=name,
                        father_name=fname,
                        dob=dob,
                        address="Imported via CSV",
                        course=course,
                        total_course_fee=total_fee,
                        course_duration_months=12 if c_type == "Annual" else 6,
                        fee_frequency="Monthly",
                        admission_date=adm_date,
                        phone="",
                        subjects="",
                        gender=gender,
                        category=category,
                        course_type=c_type
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Failed to import row: {row} -> {e}")

        if error_count > 0:
            messagebox.showwarning(
                "Import Completed with Errors", 
                f"Successfully imported {success_count} students.\nFailed to import {error_count} rows. Check console.",
                parent=parent
            )
        else:
            messagebox.showinfo(
                "Import Successful", 
                f"Successfully imported {success_count} students.",
                parent=parent
            )
        return True
    except Exception as e:
        messagebox.showerror("Import Failed", str(e), parent=parent)
        return False
