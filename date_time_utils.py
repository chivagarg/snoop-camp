from datetime import datetime
def to_human_readable_dt_format(dt):
    return "{:%a, %b %d %Y}".format(dt)

def get_today():
    return datetime.today()