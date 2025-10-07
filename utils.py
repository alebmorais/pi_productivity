from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import os

def get_tz():
    tzname = os.getenv("TIMEZONE", "UTC")
    try:
        return ZoneInfo(tzname)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")

def today_local():
    return datetime.now(get_tz()).date()

def parse_iso_date(dstr):
    # Accept 'YYYY-MM-DD' or ISO with Z/offset
    if not dstr:
        return None
    try:
        if 'T' in dstr:
            # Handles ISO 8601 format like "2025-10-05T14:48:00.000Z"
            return datetime.fromisoformat(dstr.replace('Z', '+00:00')).astimezone(get_tz()).date()
        # Handles simple date format like "2025-10-05"
        return date.fromisoformat(dstr)
    except (ValueError, TypeError):
        return None

def normalize_and_format_date(value: object | None) -> str | None:
    """Normalizes a date from various formats into an ISO string."""
    if value is None:
        return None
    
    dt = None
    if isinstance(value, (int, float)):
        try:
            dt = datetime.fromtimestamp(float(value))
        except (ValueError, OSError):
            return None
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            # Handles full ISO 8601 format
            dt = datetime.fromisoformat(candidate.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Handles simple 'YYYY-MM-DD'
                dt = datetime.strptime(candidate, '%Y-%m-%d')
            except ValueError:
                return None
    
    if dt:
        return dt.isoformat(timespec="seconds")
    return None
