"""
utils/fee_calculator.py
Pure Python business logic — no DB, no UI imports.
Calculates installment schedules, statuses, and totals.
"""

import calendar
from datetime import date

FREQUENCY_MONTHS = {
    'Monthly':     1,
    'Quarterly':   3,
    'Semi-Annual': 6,
    'Annual':      12,
}
FREQUENCIES = list(FREQUENCY_MONTHS.keys())
INSTALLMENT_OPTIONS = ["1", "2", "3", "4", "5", "6", "12"]

STATUS_STYLE = {
    'PAID':     {'label': 'PAID',     'icon': '\uE73E', 'color': '#10b981', 'bg': '#064e3b', 'light_bg': '#ecfdf5'},
    'OVERDUE':  {'label': 'OVERDUE',  'icon': '\uE7BA', 'color': '#ef4444', 'bg': '#450a0a', 'light_bg': '#fef2f2'},
    'DUE_SOON': {'label': 'DUE_SOON', 'icon': '\uE81C', 'color': '#f59e0b', 'bg': '#451a03', 'light_bg': '#fffbeb'},
    'UPCOMING': {'label': 'UPCOMING', 'icon': '\uE787', 'color': '#3b82f6', 'bg': '#1e1b4b', 'light_bg': '#eff6ff'},
}


def add_months(d: date, months: int) -> date:
    """Add months to a date — pure stdlib, no dateutil."""
    m    = d.month - 1 + months
    year = d.year + m // 12
    mon  = m % 12 + 1
    day  = min(d.day, calendar.monthrange(year, mon)[1])
    return date(year, mon, day)


def parse_date(val) -> date:
    if isinstance(val, date):
        return val
    if val is None:
        return date.today()
    return date.fromisoformat(str(val)[:10])


def compute_due_dates(n: int, admission_date: str, duration_months: int) -> list:
    adm_dt = parse_date(admission_date)
    if n <= 1:
        return [adm_dt]
    interval = max(1, duration_months // n)
    return [add_months(adm_dt, i * interval) for i in range(n)]


def calculate_installments(student: dict, payments: list) -> list:
    """
    Returns a list of installment dicts:
      no, due_date, amount_due, amount_paid, balance, status, days_diff
    Payments are allocated cumulatively oldest-first.
    """
    freq      = student.get('fee_frequency') or 'Monthly'
    duration  = int(student.get('course_duration_months') or 12)
    total_fee = float(student['total_course_fee'])
    admission = parse_date(student.get('admission_date'))

    freq_m = FREQUENCY_MONTHS.get(freq, 1)
    n      = max(1, duration // freq_m)
    if n > 5:
        n = 5
    amt    = round(total_fee / n, 2)

    # Remaining available paid pool (oldest installment gets paid first)
    remaining = sum(float(p['amount_paid']) for p in payments)
    today     = date.today()
    result    = []

    for i in range(n):
        due       = add_months(admission, freq_m * i)
        this_paid = min(remaining, amt)
        remaining = max(0.0, remaining - this_paid)
        days_diff = (due - today).days

        if this_paid >= amt - 0.01:
            status = 'PAID'
        elif due < today:
            status = 'OVERDUE'
        elif days_diff <= 30:
            status = 'DUE_SOON'
        else:
            status = 'UPCOMING'

        result.append({
            'no':          i + 1,
            'due_date':    due,
            'amount_due':  amt,
            'amount_paid': round(this_paid, 2),
            'balance':     round(amt - this_paid, 2),
            'status':      status,
            'days_diff':   days_diff,
        })

    return result


def get_overall_status(installments: list) -> str:
    if not installments:
        return 'UPCOMING'
    statuses = {i['status'] for i in installments}
    for s in ('OVERDUE', 'DUE_SOON', 'UPCOMING', 'PAID'):
        if s in statuses:
            return s
    return 'UPCOMING'


def get_next_due(installments: list) -> dict | None:
    """Return the next unpaid installment."""
    for inst in installments:
        if inst['status'] != 'PAID':
            return inst
    return None


def summary(installments: list) -> dict:
    total_due  = sum(i['amount_due']  for i in installments)
    total_paid = sum(i['amount_paid'] for i in installments)
    overdue_n  = sum(1 for i in installments if i['status'] == 'OVERDUE')
    paid_n     = sum(1 for i in installments if i['status'] == 'PAID')
    pct        = (total_paid / total_due * 100) if total_due else 0
    return {
        'total_due':   total_due,
        'total_paid':  total_paid,
        'balance':     total_due - total_paid,
        'overdue_n':   overdue_n,
        'paid_n':      paid_n,
        'pct':         pct,
        'n_inst':      len(installments),
    }
