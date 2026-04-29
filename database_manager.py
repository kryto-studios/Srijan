"""
database_manager.py
-------------------
Handles all MySQL interactions for the Student Fee Management System.
Completely decoupled from the UI layer.
"""

import mysql.connector
from mysql.connector import Error
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Configuration – update these if your MySQL setup differs
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "1123",          # <-- change if you have a password
    "database": "fee_management",
    "port":     3306,
}


class DatabaseManager:
    """Manages all database operations using a persistent connection."""

    def __init__(self):
        self.connection = None
        self.connect()

    # ------------------------------------------------------------------ #
    #  Connection                                                          #
    # ------------------------------------------------------------------ #

    def connect(self):
        """Establish a connection, create DB/tables if missing, and run column migrations."""
        try:
            temp_config = DB_CONFIG.copy()
            db_name = temp_config.pop("database")

            conn   = mysql.connector.connect(**temp_config)
            cursor = conn.cursor()

            # Create DB & tables
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.execute(f"USE {db_name}")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id               INT AUTO_INCREMENT PRIMARY KEY,
                    name             VARCHAR(100)   NOT NULL,
                    father_name      VARCHAR(100)   NOT NULL,
                    dob              DATE           NOT NULL,
                    phone            VARCHAR(20)    DEFAULT '',
                    address          TEXT           NOT NULL,
                    course           VARCHAR(100)   NOT NULL,
                    total_course_fee DECIMAL(10,2)  NOT NULL,
                    enrolled_on      TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                    course_duration_months INT      DEFAULT 12,
                    fee_frequency    VARCHAR(20)    DEFAULT 'Monthly',
                    admission_date   DATE,
                    gender           VARCHAR(20)    DEFAULT 'Not Specified',
                    category         VARCHAR(20)    DEFAULT 'General',
                    member_id        VARCHAR(50)    DEFAULT '',
                    course_type      VARCHAR(50)    DEFAULT 'Annual'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    p_id         INT AUTO_INCREMENT PRIMARY KEY,
                    student_id   INT            NOT NULL,
                    amount_paid  DECIMAL(10,2)  NOT NULL,
                    payment_date DATE           NOT NULL,
                    month_name   VARCHAR(20)    DEFAULT '',
                    CONSTRAINT fk_student FOREIGN KEY (student_id)
                        REFERENCES students(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)

            # Add payment_info column safely (migration)
            try:
                cursor.execute("ALTER TABLE payments ADD COLUMN payment_info VARCHAR(100) DEFAULT ''")
            except Error:
                pass  # column already exists

            # Ensure month_name column exists (migration for older DBs)
            try:
                cursor.execute("ALTER TABLE payments ADD COLUMN month_name VARCHAR(20) DEFAULT ''")
            except Error:
                pass  # column already exists

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS installment_schedules (
                    id             INT AUTO_INCREMENT PRIMARY KEY,
                    student_id     INT            NOT NULL,
                    inst_no        INT            NOT NULL,
                    due_date       DATE           NOT NULL,
                    amount_due     DECIMAL(10,2)  NOT NULL,
                    amount_paid    DECIMAL(10,2)  NOT NULL DEFAULT 0,
                    split_due_date DATE           DEFAULT NULL,
                    created_at     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_inst_student FOREIGN KEY (student_id)
                        REFERENCES students(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id             INT AUTO_INCREMENT PRIMARY KEY,
                    invoice_no     VARCHAR(50)    NOT NULL,
                    student_id     INT            NOT NULL,
                    student_name   VARCHAR(100)   NOT NULL,
                    invoice_date   DATE           NOT NULL,
                    due_date       DATE           NOT NULL,
                    base_amount    DECIMAL(10,2)  NOT NULL,
                    discount       DECIMAL(10,2)  DEFAULT 0,
                    gst_pct        DECIMAL(5,2)   DEFAULT 0,
                    amount_paid    DECIMAL(10,2)  NOT NULL,
                    amount_due     DECIMAL(10,2)  NOT NULL,
                    payment_mode   VARCHAR(50)    DEFAULT 'Pending',
                    file_path      TEXT           NOT NULL,
                    created_at     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_inv_student FOREIGN KEY (student_id)
                        REFERENCES students(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'staff'
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                import hashlib
                pw_hash = hashlib.sha256("admin".encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES ('admin', %s, 'admin')", 
                    (pw_hash,)
                )

            # Column migrations (safe — silently skip if column exists)
            migrations = [
                "ALTER TABLE students ADD COLUMN course_duration_months INT DEFAULT 12",
                "ALTER TABLE students ADD COLUMN fee_frequency VARCHAR(20) DEFAULT 'Monthly'",
                "ALTER TABLE students ADD COLUMN admission_date DATE",
                "ALTER TABLE students ADD COLUMN phone VARCHAR(20) DEFAULT ''",
                "ALTER TABLE students ADD COLUMN subjects VARCHAR(500)",
                "ALTER TABLE students ADD COLUMN gender VARCHAR(20) DEFAULT 'Not Specified'",
                "ALTER TABLE students ADD COLUMN category VARCHAR(20) DEFAULT 'General'",
                "ALTER TABLE students ADD COLUMN member_id VARCHAR(50) DEFAULT ''",
                "ALTER TABLE students ADD COLUMN course_type VARCHAR(50) DEFAULT 'Annual'",
                # Widen phone to hold student + parent combined (e.g. '9876543210 / P:9876543210')
                "ALTER TABLE students MODIFY COLUMN phone VARCHAR(60) DEFAULT ''",
            ]
            for sql in migrations:
                try:
                    cursor.execute(sql)
                except Error:
                    pass  # column already exists

            # Back-fill nulls for existing rows
            cursor.execute("UPDATE students SET admission_date = DATE(enrolled_on) WHERE admission_date IS NULL")
            cursor.execute("UPDATE students SET course_duration_months = 12 WHERE course_duration_months IS NULL")
            cursor.execute("UPDATE students SET fee_frequency = 'Monthly' WHERE fee_frequency IS NULL")

            conn.commit()
            cursor.close()
            conn.close()

            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print(f"[DB] Connected to '{db_name}'.")

        except Error as e:
            raise ConnectionError(
                f"MySQL Connection/Setup Error: {e}\n\n"
                f"Please ensure MySQL is running on localhost:3306\n"
                f"and your password in DB_CONFIG is correct."
            )


    def _ensure_connection(self):
        """Re-connect if the connection was dropped."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
        except Error:
            self.connect()

    def close(self):
        """Gracefully close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[DB] Connection closed.")

    # ------------------------------------------------------------------ #
    #  Authentication                                                      #
    # ------------------------------------------------------------------ #

    def authenticate(self, username: str, password: str) -> dict | None:
        """Verify username and password, return user dict if valid."""
        import hashlib
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        self._ensure_connection()
        sql = "SELECT id, username, role FROM users WHERE username = %s AND password_hash = %s"
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (username, pw_hash))
            return cursor.fetchone()
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Student Operations                                                  #
    # ------------------------------------------------------------------ #

    def add_student(self, name: str, father_name: str, dob: str,
                    address: str, course: str, total_course_fee: float,
                    course_duration_months: int = 12,
                    fee_frequency: str = "Monthly",
                    admission_date: str = None,
                    phone: str = "",
                    subjects: str = "",
                    gender: str = "Not Specified",
                    category: str = "General",
                    course_type: str = "Annual") -> int:
        """Insert a new student record and generate Member ID. Returns the new student ID."""
        self._ensure_connection()
        from datetime import date as _date
        if not admission_date:
            admission_date = str(_date.today())
        sql = """
            INSERT INTO students
              (name, father_name, dob, address, course, total_course_fee,
               course_duration_months, fee_frequency, admission_date, phone, subjects, gender, category, course_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, (name, father_name, dob, address, course,
                                 total_course_fee, course_duration_months,
                                 fee_frequency, admission_date, phone, subjects, gender, category, course_type))
            self.connection.commit()
            new_id = cursor.lastrowid
            
            # Generate Member ID
            year_str = str(_date.today().year)[-2:]
            class_code = "13"
            if course == "12th": class_code = "12"
            elif course == "11th": class_code = "11"
            elif course == "10th": class_code = "10"
            elif course == "9th": class_code = "09"
            elif course == "8th": class_code = "08"
            elif course == "7th": class_code = "07"
            elif course == "6th": class_code = "06"
            
            member_id = f"SRJN{year_str}{class_code}{new_id:03d}"
            cursor.execute("UPDATE students SET member_id = %s WHERE id = %s", (member_id, new_id))
            self.connection.commit()
            
            return new_id
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to add student: {e}")
        finally:
            cursor.close()

    def get_all_students(self) -> list[dict]:
        """Return all students as a list of dicts."""
        self._ensure_connection()
        sql = """
            SELECT s.id, s.name, s.father_name, s.dob, s.address, s.phone,
                   s.course, s.subjects, s.gender, s.category, s.member_id, s.course_type, s.total_course_fee,
                   COALESCE(SUM(p.amount_paid), 0)                          AS total_paid,
                   s.total_course_fee - COALESCE(SUM(p.amount_paid), 0)     AS balance
            FROM students s
            LEFT JOIN payments p ON s.id = p.student_id
            GROUP BY s.id
            ORDER BY s.id
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Failed to fetch students: {e}")
        finally:
            cursor.close()

    def search_students(self, query: str = "", course: str = "All") -> list[dict]:
        """Search / filter students by name/ID and optionally by course."""
        self._ensure_connection()
        params = []
        conditions = []

        if query.strip():
            conditions.append("(s.name LIKE %s OR CAST(s.id AS CHAR) LIKE %s)")
            like = f"%{query.strip()}%"
            params.extend([like, like])

        if course and course != "All":
            conditions.append("s.course = %s")
            params.append(course)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        sql = f"""
            SELECT s.id, s.name, s.father_name, s.dob, s.address, s.phone,
                   s.course, s.subjects, s.gender, s.category, s.member_id, s.course_type, s.total_course_fee,
                   COALESCE(s.course_duration_months, 12)  AS course_duration_months,
                   COALESCE(s.fee_frequency, 'Monthly')    AS fee_frequency,
                   s.admission_date,
                   COALESCE(SUM(p.amount_paid), 0)         AS total_paid,
                   s.total_course_fee - COALESCE(SUM(p.amount_paid), 0) AS balance
            FROM students s
            LEFT JOIN payments p ON s.id = p.student_id
            {where_clause}
            GROUP BY s.id
            ORDER BY s.name
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Search failed: {e}")
        finally:
            cursor.close()

    def get_student_by_id(self, student_id: int) -> dict | None:
        """Return a single student's full record by ID."""
        self._ensure_connection()
        sql = """
            SELECT s.id, s.name, s.father_name, s.dob, s.address, s.phone,
                   s.course, s.subjects, s.gender, s.category, s.member_id, s.course_type, s.total_course_fee,
                   COALESCE(s.course_duration_months, 12)  AS course_duration_months,
                   COALESCE(s.fee_frequency, 'Monthly')    AS fee_frequency,
                   s.admission_date,
                   COALESCE(SUM(p.amount_paid), 0)         AS total_paid,
                   s.total_course_fee - COALESCE(SUM(p.amount_paid), 0) AS balance
            FROM students s
            LEFT JOIN payments p ON s.id = p.student_id
            WHERE s.id = %s
            GROUP BY s.id
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (student_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def get_all_courses(self) -> list[str]:
        """Return a distinct list of all courses."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT DISTINCT course FROM students ORDER BY course")
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Payment Operations                                                  #
    # ------------------------------------------------------------------ #

    def add_payment(self, student_id: int, amount_paid: float,
                    payment_date: str, month_name: str) -> int:
        """Insert a new payment record. Returns the new payment ID."""
        self._ensure_connection()
        sql = """
            INSERT INTO payments (student_id, amount_paid, payment_date, month_name)
            VALUES (%s, %s, %s, %s)
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, (student_id, amount_paid, payment_date, month_name))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to add payment: {e}")
        finally:
            cursor.close()

    def get_payments_for_student(self, student_id: int) -> list[dict]:
        """Return all payment records for a given student."""
        self._ensure_connection()
        sql = """
            SELECT *
            FROM payments
            WHERE student_id = %s
            ORDER BY payment_date DESC
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (student_id,))
            rows = cursor.fetchall()
            # Ensure month_name key always exists (backward compat)
            for r in rows:
                if 'month_name' not in r or r['month_name'] is None:
                    r['month_name'] = r.get('payment_info', '—')
            return rows
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Installment Management                                              #
    # ------------------------------------------------------------------ #

    def create_installment_schedule(self, student_id: int, n: int, total_fee: float, admission_date: str, duration_months: int) -> None:
        from utils.fee_calculator import compute_due_dates
        self._ensure_connection()
        amt = round(total_fee / n, 2)
        due_dates = compute_due_dates(n, admission_date, duration_months)
        cursor = self.connection.cursor()
        try:
            for i, dd in enumerate(due_dates):
                cursor.execute("""
                    INSERT INTO installment_schedules (student_id, inst_no, due_date, amount_due)
                    VALUES (%s, %s, %s, %s)
                """, (student_id, i + 1, str(dd), amt))
            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to create schedule: {e}")
        finally:
            cursor.close()

    def create_installment_schedule_custom(self, student_id: int, due_dates: list, amounts: list) -> None:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            for i, (dd, amt) in enumerate(zip(due_dates, amounts)):
                cursor.execute("""
                    INSERT INTO installment_schedules (student_id, inst_no, due_date, amount_due)
                    VALUES (%s, %s, %s, %s)
                """, (student_id, i + 1, str(dd), round(amt, 2)))
            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to create custom schedule: {e}")
        finally:
            cursor.close()

    def get_installments(self, student_id: int) -> list:
        self._ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM installment_schedules
                WHERE student_id = %s ORDER BY inst_no
            """, (student_id,))
            rows = cursor.fetchall()
            today = date.today()
            has_past_due = False
            for r in rows:
                paid    = float(r['amount_paid'])
                due_amt = float(r['amount_due'])
                dd      = r['due_date']
                
                if isinstance(dd, str):
                    dd = date.fromisoformat(dd[:10])

                if paid >= due_amt - 0.01:
                    r['status'] = 'PAID'
                else:
                    if has_past_due:
                        r['status'] = 'OVERDUE'
                    elif paid > 0:
                        if dd < today:
                            r['status'] = 'OVERDUE'
                            has_past_due = True
                        else:
                            r['status'] = 'PARTIAL'
                    elif dd < today:
                        r['status'] = 'OVERDUE'
                        has_past_due = True
                    elif dd <= today + timedelta(days=3):
                        r['status'] = 'DUE SOON'
                    else:
                        r['status'] = 'UPCOMING'
            return rows
        finally:
            cursor.close()

    def update_installment(self, inst_id: int, due_date: str, amount_due: float) -> None:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                UPDATE installment_schedules
                SET due_date = %s, amount_due = %s
                WHERE id = %s
            """, (due_date, amount_due, inst_id))
            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to update installment: {e}")
        finally:
            cursor.close()

    def mark_installment_split(self, inst_id: int, split_due_date: str) -> None:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                UPDATE installment_schedules
                SET split_due_date = %s
                WHERE id = %s
            """, (split_due_date, inst_id))
            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to set split date: {e}")
        finally:
            cursor.close()

    def record_installment_payment(self, inst_id: int, amount: float, payment_date: str, split_due_date: str = None, payment_info: str = None) -> None:
        self._ensure_connection()
        read_cur = self.connection.cursor(dictionary=True)
        try:
            read_cur.execute("SELECT * FROM installment_schedules WHERE id = %s", (inst_id,))
            inst = read_cur.fetchone()
            if not inst:
                raise ValueError("Installment not found.")
        finally:
            read_cur.close()

        write_cur = self.connection.cursor()
        try:
            new_paid = float(inst['amount_paid']) + amount
            due_amt = float(inst['amount_due'])
            
            # If payment covers remaining balance, clear split_due_date
            if new_paid >= due_amt - 0.01:
                split_due_date = None
                
            write_cur.execute("""
                UPDATE installment_schedules
                SET amount_paid = %s, split_due_date = %s
                WHERE id = %s
            """, (new_paid, split_due_date, inst_id))
            
            info_str = payment_info or f"Inst #{inst['inst_no']}"
            try:
                write_cur.execute("""
                    INSERT INTO payments (student_id, amount_paid, payment_date, payment_info)
                    VALUES (%s, %s, %s, %s)
                """, (inst['student_id'], amount, payment_date, info_str))
            except Error as first_err:
                try:
                    write_cur.execute("""
                        INSERT INTO payments (student_id, amount_paid, payment_date, month_name)
                        VALUES (%s, %s, %s, %s)
                    """, (inst['student_id'], amount, payment_date, info_str))
                except Error as second_err:
                    raise RuntimeError(f"Payment insert failed: {first_err} | {second_err}")
            self.connection.commit()
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Payment failed: {e}")
        finally:
            write_cur.close()

    def get_upcoming_installment_reminders(self) -> list:
        from datetime import date, timedelta
        self._ensure_connection()
        today   = date.today()
        in_7    = today + timedelta(days=7)
        cursor  = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT i.*, s.name AS student_name, s.phone, s.course
                FROM installment_schedules i
                JOIN students s ON i.student_id = s.id
                WHERE i.amount_paid < i.amount_due
                  AND (
                      i.due_date <= %s
                      OR (i.split_due_date IS NOT NULL AND i.split_due_date <= %s)
                  )
                ORDER BY i.due_date
            """, (in_7, in_7))
            rows = cursor.fetchall()
            for r in rows:
                paid = float(r['amount_paid'])
                due  = float(r['amount_due'])
                dd   = r['due_date']
                if paid >= due - 0.01:
                    r['status'] = 'PAID'
                elif paid > 0:
                    r['status'] = 'PARTIAL' if dd >= today else 'OVERDUE'
                elif dd < today:
                    r['status'] = 'OVERDUE'
                else:
                    days_left = (dd - today).days if hasattr(dd, 'date') else 99
                    if days_left <= 3:
                        r['status'] = 'DUE SOON'
                    else:
                        r['status'] = 'UPCOMING'
            return [r for r in rows if r['status'] not in ('PAID', 'UPCOMING')]
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Dashboard Statistics                                                #
    # ------------------------------------------------------------------ #

    def get_dashboard_stats(self, inst_filter: int = None) -> dict:
        """Return aggregate statistics for the dashboard, including calculated overdue based on installments."""
        self._ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            # We calculate all totals dynamically from the installments table
            cursor.execute("""
                SELECT i.id, i.student_id, i.inst_no, i.due_date, i.amount_due, i.amount_paid, s.name 
                FROM installment_schedules i
                JOIN students s ON i.student_id = s.id
                ORDER BY i.student_id, i.inst_no
            """)
            rows = cursor.fetchall()
            
            from itertools import groupby
            from datetime import date
            today = date.today()
            
            total_collected = 0.0
            total_pending = 0.0
            total_students_set = set()
            
            total_overdue = 0.0
            overdue_students = 0
            overdue_details = []
            
            for sid, group in groupby(rows, key=lambda x: x["student_id"]):
                has_past_due = False
                s_overdue = 0.0
                overdue_count = 0
                s_name = ""
                
                for r in group:
                    s_name  = r["name"]
                    paid    = float(r["amount_paid"])
                    due_amt = float(r["amount_due"])
                    dd      = r["due_date"]
                    if isinstance(dd, str):
                        dd = date.fromisoformat(dd[:10])
                        
                    is_overdue = False
                    if paid >= due_amt - 0.01:
                        pass
                    else:
                        if has_past_due:
                            is_overdue = True
                        elif paid > 0:
                            if dd < today:
                                is_overdue = True
                                has_past_due = True
                        elif dd < today:
                            is_overdue = True
                            has_past_due = True
                            
                    if is_overdue:
                        # Only add to cascading overdue stats if this installment matches filter
                        if inst_filter is None or r["inst_no"] == inst_filter:
                            s_overdue += (due_amt - paid)
                            overdue_count += 1
                    
                    if inst_filter is None or r["inst_no"] == inst_filter:
                        total_collected += paid
                        total_pending += max(0, due_amt - paid)
                        total_students_set.add(sid)
                        
                if s_overdue > 0:
                    total_overdue += s_overdue
                    overdue_students += 1
                    overdue_details.append({
                        "id": sid,
                        "name": s_name,
                        "amount": s_overdue,
                        "months": overdue_count  # using 'months' key for compatibility with UI
                    })

            return {
                "total_students":   len(total_students_set),
                "total_collected":  total_collected,
                "total_pending":    total_pending,
                "total_overdue":    total_overdue,
                "overdue_students": overdue_students,
                "overdue_details":  overdue_details
            }
        except Error as e:
            raise RuntimeError(f"Failed to get dashboard stats: {e}")
        finally:
            cursor.close()

    def get_course_distribution(self) -> dict:
        """Return the count of students per course for analytics."""
        self._ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT course, COUNT(*) as count FROM students GROUP BY course")
            return {row["course"]: row["count"] for row in cursor.fetchall()}
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Defaulter Tracking                                                  #
    # ------------------------------------------------------------------ #

    def get_defaulters(self, month_name: str) -> list[dict]:
        """Return students who have NOT made any payment in the given month."""
        self._ensure_connection()
        sql = """
            SELECT s.id, s.name, s.father_name, s.course, s.total_course_fee, s.phone,
                   s.gender, s.category, s.member_id, s.course_type,
                   COALESCE(s.course_duration_months, 12)  AS course_duration_months,
                   COALESCE(s.fee_frequency, 'Monthly')    AS fee_frequency,
                   s.admission_date,
                   COALESCE(SUM(p_all.amount_paid), 0)                              AS total_paid,
                   s.total_course_fee - COALESCE(SUM(p_all.amount_paid), 0)         AS balance
            FROM students s
            LEFT JOIN payments p_all ON s.id = p_all.student_id
            WHERE s.id NOT IN (
                SELECT DISTINCT student_id
                FROM payments
                WHERE month_name = %s
            )
            GROUP BY s.id
            ORDER BY s.name
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (month_name,))
            return cursor.fetchall()
        except Error as e:
            raise RuntimeError(f"Failed to get defaulters: {e}")
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Monthly Status (for 12-month calendar view)                        #
    # ------------------------------------------------------------------ #

    def get_monthly_status(self, student_id: int, year: int) -> dict:
        """
        Return a dict mapping month_name -> total_amount_paid
        for a specific student in a given year.
        Months with no payment are not included (check with .get()).
        """
        self._ensure_connection()
        sql = """
            SELECT month_name, SUM(amount_paid) AS total
            FROM payments
            WHERE student_id = %s
              AND YEAR(payment_date) = %s
            GROUP BY month_name
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (student_id, year))
            return {row["month_name"]: float(row["total"]) for row in cursor.fetchall()}
        except Error as e:
            raise RuntimeError(f"Failed to get monthly status: {e}")
        finally:
            cursor.close()

    def get_payment_by_id(self, p_id: int) -> dict | None:
        """Return a single payment record by its primary key."""
        self._ensure_connection()
        sql = "SELECT * FROM payments WHERE p_id = %s"
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (p_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def delete_student(self, student_id: int) -> bool:
        """Delete a student and all their payment records (cascade). Returns True on success."""
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to delete student: {e}")
        finally:
            cursor.close()

    # -----------------------------------------------------------------------
    # INVOICE MANAGEMENT
    # -----------------------------------------------------------------------

    def save_invoice_record(self, data: dict) -> int:
        """Save a generated invoice to the database."""
        self._ensure_connection()
        sql = """
            INSERT INTO invoices (
                invoice_no, student_id, student_name, invoice_date, due_date,
                base_amount, discount, gst_pct, amount_paid, amount_due,
                payment_mode, file_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, (
                data.get("invoice_no"),
                data.get("student_id"),
                data.get("student_name"),
                data.get("invoice_date"),
                data.get("due_date"),
                data.get("base_amount", 0),
                data.get("discount", 0),
                data.get("gst_pct", 0),
                data.get("amount_paid", 0),
                data.get("amount_due", 0),
                data.get("received_mode", "Pending"),
                data.get("save_path", "")
            ))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            raise Exception(f"Database error saving invoice: {e}")
        finally:
            cursor.close()

    def search_invoices(self, query: str = "") -> list:
        """Return invoices matching the search query."""
        self._ensure_connection()
        
        sql = """
            SELECT id, invoice_no, student_id, student_name, invoice_date, due_date,
                   base_amount, discount, gst_pct, amount_paid, amount_due, payment_mode, file_path, created_at
            FROM invoices
        """
        params = []
        
        if query:
            sql += """
                WHERE invoice_no LIKE %s
                   OR student_name LIKE %s
                   OR CAST(student_id AS CHAR) LIKE %s
                   OR CAST(invoice_date AS CHAR) LIKE %s
            """
            like_q = f"%{query}%"
            params.extend([like_q, like_q, like_q, like_q])
            
        sql += " ORDER BY created_at DESC"
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Error as e:
            raise Exception(f"Database error searching invoices: {e}")
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Danger Zone                                                         #
    # ------------------------------------------------------------------ #

    def clear_all_student_data(self) -> int:
        """Delete ALL student records and related data. Returns count of deleted students.
        Tables cleared: installment_schedules, payments, invoices, students.
        Users table is preserved.
        """
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM students")
            count = cursor.fetchone()[0]
            # Disable FK checks, truncate all related tables, re-enable
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in ["installment_schedules", "payments", "invoices", "students"]:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table}")
                except Error:
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                    except Error:
                        pass
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            self.connection.commit()
            return count
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to clear database: {e}")
        finally:
            cursor.close()
