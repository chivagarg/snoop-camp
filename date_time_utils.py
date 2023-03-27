from datetime import datetime

def to_human_readable_dt_format(date: datetime) -> str:
    return date.strftime('%a, %b %d %Y')

def get_today() -> datetime:
    return datetime.today()