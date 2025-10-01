from datetime import datetime, timezone, date
import pytz, os

def get_tz():
    tzname = os.getenv("TIMEZONE","UTC")
    try:
        return pytz.timezone(tzname)
    except Exception:
        return pytz.UTC

def today_local():
    tz = get_tz()
    return datetime.now(tz).date()

def parse_iso_date(dstr):
    # Accept 'YYYY-MM-DD' or ISO with Z/offset
    if not dstr: return None
    try:
        if 'T' in dstr:
            ds = dstr.replace('Z','+00:00')
            return datetime.fromisoformat(ds).astimezone(get_tz()).date()
        return datetime.fromisoformat(dstr).date()
    except Exception:
        return None
