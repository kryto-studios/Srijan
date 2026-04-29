-- ============================================================
-- Student Fee Management System - Database Setup Script
-- Run this script in MySQL before launching the application.
-- ============================================================

CREATE DATABASE IF NOT EXISTS fee_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fee_management;

-- -------------------------------------------------------
-- Table: students
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    father_name     VARCHAR(100)    NOT NULL,
    dob             DATE            NOT NULL,
    address         TEXT            NOT NULL,
    course          VARCHAR(100)    NOT NULL,
    total_course_fee DECIMAL(10, 2) NOT NULL,
    enrolled_on     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- Table: payments
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    p_id            INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT             NOT NULL,
    amount_paid     DECIMAL(10, 2)  NOT NULL,
    payment_date    DATE            NOT NULL,
    month_name      VARCHAR(20)     NOT NULL,
    CONSTRAINT fk_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- Sample Data (Optional - comment out if not needed)
-- -------------------------------------------------------
INSERT INTO students (name, father_name, dob, address, course, total_course_fee) VALUES
('Aarav Sharma',   'Rajesh Sharma',   '2005-03-15', '12 MG Road, Delhi',       'B.Sc Computer Science', 45000.00),
('Priya Verma',    'Suresh Verma',    '2004-11-22', '45 Nehru Nagar, Jaipur',  'B.Com',                 30000.00),
('Rohan Gupta',    'Anil Gupta',      '2005-07-10', '78 Civil Lines, Agra',    'BCA',                   40000.00),
('Sneha Patel',    'Mahesh Patel',    '2006-01-08', '22 Ring Road, Surat',     'B.Sc Computer Science', 45000.00),
('Arjun Singh',    'Vijay Singh',     '2004-09-30', '55 Lal Kothi, Jaipur',   'MBA',                   80000.00);

INSERT INTO payments (student_id, amount_paid, payment_date, month_name) VALUES
(1, 5000.00, '2026-04-01', 'April'),
(1, 5000.00, '2026-03-05', 'March'),
(2, 3000.00, '2026-04-03', 'April'),
(3, 4000.00, '2026-03-10', 'March'),
(5, 8000.00, '2026-04-12', 'April'),
(5, 8000.00, '2026-03-08', 'March');
