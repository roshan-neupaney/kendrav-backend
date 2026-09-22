from zoneinfo import ZoneInfo


def convert_to_user_timezone(user_timezone, date_time):
    dt_local = date_time.replace(tzinfo=ZoneInfo(user_timezone))
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    return dt_utc
