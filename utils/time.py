from datetime import datetime, timezone, timedelta

# IST = UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

def now_utc():
    return datetime.utcnow()

def now_ist():
    return datetime.now(IST)

def to_ist(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)

def seconds_remaining(dt):
    if not dt:
        return None
    return int((dt - now_utc()).total_seconds())

def is_expired(dt):
    if not dt:
        return False
    return now_utc() > dt
