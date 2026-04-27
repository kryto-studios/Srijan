"""
database_manager.py
-------------------
Handles all MySQL interactions for the Student Fee Management System.
Completely decoupled from the UI layer.
"""

import mysql.connector
from mysql.connector import Error
from datetime import date


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
                    address          TEXT           NOT NULL,
                    course           VARCHAR(100)   NOT NULL,
                    total_course_fee DECIMAL(10,2)  NOT NULL,
                    enrolled_on      TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                    course_duration_months INT      DEFAULT 12,
                    fee_frequency    VARCHAR(20)    DEFAULT 'Monthly',
                    admission_date   DATE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    p_id         INT AUTO_INCREMENT PRIMARY KEY,
                    student_id   INT            NOT NULL,
                    amount_paid  DECIMAL(10,2)  NOT NULL,
                    payment_date DATE           NOT NULL,
                    month_name   VARCHAR(20)    NOT NULL,
                    CONSTRAINT fk_student FOREIGN KEY (student_id)
                        REFERENCES students(id) ON DELETE CASCADE ON UPDATE CASCADE
                )
            """)

            # Column migrations (safe — silently skip if column exists)
            migrations = [
                "ALTER TABLE students ADD COLUMN course_duration_months INT DEFAULT 12",
                "ALTER TABLE students ADD COLUMN fee_frequency VARCHAR(20) DEFAULT 'Monthly'",
                "ALTER TABLE students ADD COLUMN admission_date DATE",
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
    #  Student Operations                                                  #
    # ------------------------------------------------------------------ #

    def add_student(self, name: str, father_name: str, dob: str,
                    address: str, course: str, total_course_fee: float,
                    course_duration_months: int = 12,
                    fee_frequency: str = "Monthly",
                    admission_date: str = None) -> int:
        """Insert a new student record. Returns the new student ID."""
        self._ensure_connection()
        from datetime import date as _date
        if not admission_date:
            admission_date = str(_date.today())
        sql = """
            INSERT INTO students
              (name, father_name, dob, address, course, total_course_fee,
               course_duration_months, fee_frequency, admission_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, (name, father_name, dob, address, course,
                                 total_course_fee, course_duration_months,
                                 fee_frequency, admission_date))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Failed to add student: {e}")
        finally:
            cursor.close()

    def get_all_students(self) -> list[dict]:
        """Return all students as a list of dicts."""
        self._ensure_connection()
        sql = """
            SELECT s.id, s.name, s.father_name, s.dob, s.address,
                   s.course, s.total_course_fee,
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
            SELECT s.id, s.name, s.father_name, s.dob, s.address,
                   s.course, s.total_course_fee,
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
            SELECT s.id, s.name, s.father_name, s.dob, s.address,
                   s.course, s.total_course_fee,
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
            SELECT p_id, amount_paid, payment_date, month_name
            FROM payments
            WHERE student_id = %s
            ORDER BY payment_date DESC
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (student_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # ------------------------------------------------------------------ #
    #  Dashboard Statistics                                                #
    # ------------------------------------------------------------------ #

    def get_dashboard_stats(self) -> dict:
        """Return aggregate statistics for the dashboard, including calculated overdue."""
        from utils.fee_calculator import calculate_installments
        self._ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Basic stats
            cursor.execute("SELECT COUNT(*) AS total_students FROM students")
            total_students = cursor.fetchone()["total_students"]

            cursor.execute("SELECT COALESCE(SUM(amount_paid), 0) AS total_collected FROM payments")
            total_collected = float(cursor.fetchone()["total_collected"])

            cursor.execute("""
                SELECT COALESCE(SUM(s.total_course_fee - COALESCE(sub.paid, 0)), 0) AS total_pending
                FROM students s
                LEFT JOIN (
                    SELECT student_id, SUM(amount_paid) AS paid
                    FROM payments
                    GROUP BY student_id
                ) sub ON s.id = sub.student_id
            """)
            res = cursor.fetchone()
            total_pending = float(res["total_pending"]) if res and res["total_pending"] is not None else 0.0
            
            # Dynamic Overdue Calculation
            cursor.execute("""
                SELECT s.*, COALESCE(SUM(p.amount_paid), 0) as total_paid
                FROM students s
                LEFT JOIN payments p ON s.id = p.student_id
                GROUP BY s.id
            """)
            students = cursor.fetchall()
            
            cursor.execute("SELECT * FROM payments")
            all_payments = cursor.fetchall()
            # Group payments by student
            payments_by_student = {}
            for p in all_payments:
                payments_by_student.setdefault(p['student_id'], []).append(p)
                
            total_overdue = 0.0
            overdue_students = 0
            overdue_details = []
            
            for s in students:
                p_list = payments_by_student.get(s['id'], [])
                insts = calculate_installments(s, p_list)
                
                # Check for overdue installments
                overdue_insts = [i for i in insts if i['status'] == 'OVERDUE']
                s_overdue = sum(i['amount_due'] - i['amount_paid'] for i in overdue_insts)
                if s_overdue > 0:
                    total_overdue += s_overdue
                    overdue_students += 1
                    overdue_details.append({
                        "id": s['id'],
                        "name": s['name'],
                        "amount": s_overdue,
                        "months": len(overdue_insts)
                    })

            return {
                "total_students":   total_students,
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

    # ------------------------------------------------------------------ #
    #  Defaulter Tracking                                                  #
    # ------------------------------------------------------------------ #

    def get_defaulters(self, month_name: str) -> list[dict]:
        """Return students who have NOT made any payment in the given month."""
        self._ensure_connection()
        sql = """
            SELECT s.id, s.name, s.father_name, s.course, s.total_course_fee,
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

