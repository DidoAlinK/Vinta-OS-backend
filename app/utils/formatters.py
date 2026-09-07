"""
Vinta School OS — Formatters & Helpers
Phone (+213), Currency (DZD), Date/Time utilities for Algeria locale.
"""
import re
from datetime import datetime, date, timedelta, timezone


# --- Phone Formatting ---

PHONE_PATTERN = re.compile(r"^(\+213|0)?(\d{9})$")


def format_phone(phone: str) -> str:
    """
    Normalize an Algerian phone number to +213XXXXXXXXX format.
    Accepts: 0555123456, 555123456, +213555123456
    Returns: +213555123456
    """
    if not phone:
        return phone

    digits = re.sub(r"[^\d]", "", phone)

    # Remove leading 0
    if digits.startswith("0") and len(digits) == 10:
        digits = digits[1:]

    # Add country code if missing
    if not digits.startswith("213"):
        digits = "213" + digits

    return f"+{digits}"


def validate_phone(phone: str) -> bool:
    """Validate an Algerian phone number format."""
    if not phone:
        return True  # Optional field
    return bool(PHONE_PATTERN.match(phone))


# --- Currency Formatting ---

def format_dzd(amount: int) -> str:
    """Format amount in Algerian Dinars with comma separators."""
    return f"{amount:,} DA"


def parse_dzd(amount_str: str) -> int:
    """Parse a DZD amount string (e.g., '3,500 DA' or '3500') to integer."""
    cleaned = re.sub(r"[^\d]", "", amount_str)
    return int(cleaned) if cleaned else 0


# --- Date/Time Utilities ---

def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def today() -> date:
    """Get today's date in the server timezone."""
    return date.today()


def days_until(target_date: date) -> int:
    """Calculate days until a target date. Negative if past."""
    delta = target_date - today()
    return delta.days


def days_overdue(due_date: date) -> int:
    """Calculate how many days overdue a due date is. 0 if not overdue."""
    delta = today() - due_date
    return max(0, delta.days)


def overdue_bucket(days: int) -> str:
    """
    Classify overdue days into aging buckets:
    1-7d → 'recent', 8-30d → 'aging', 30d+ → 'critical'
    """
    if days <= 7:
        return "recent"
    elif days <= 30:
        return "aging"
    else:
        return "critical"


def week_date_range() -> tuple[date, date]:
    """Get the start (Sunday) and end (Saturday) of the current week."""
    t = today()
    start = t - timedelta(days=t.weekday() + 1)  # Sunday
    end = start + timedelta(days=6)  # Saturday
    return start, end


def month_date_range() -> tuple[date, date]:
    """Get the first and last day of the current month."""
    t = today()
    first_day = t.replace(day=1)
    if t.month == 12:
        last_day = t.replace(year=t.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = t.replace(month=t.month + 1, day=1) - timedelta(days=1)
    return first_day, last_day


def next_occurrence(day_of_week: int) -> date:
    """
    Get the next occurrence of a day of the week.
    day_of_week: 0=Sun, 1=Mon, ..., 6=Sat
    """
    t = today()
    days_ahead = day_of_week - t.weekday() - 1  # Adjust for Sunday=0
    if days_ahead < 0:
        days_ahead += 7
    return t + timedelta(days=days_ahead)


# --- Session Duration ---

def session_duration_hours(start_time, end_time) -> float:
    """Calculate session duration in hours from time objects."""
    from datetime import datetime as dt
    dummy = dt.today().date()
    start_dt = dt.combine(dummy, start_time)
    end_dt = dt.combine(dummy, end_time)
    delta = end_dt - start_dt
    return round(delta.total_seconds() / 3600, 2)
