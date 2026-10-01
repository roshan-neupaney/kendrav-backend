from zoneinfo import ZoneInfo
from workspaces.models import MyTime
from datetime import datetime, timezone, timedelta
from .models import Post


def convert_to_user_timezone(user_timezone, date_time):
    dt_local = date_time.replace(tzinfo=ZoneInfo(user_timezone))
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
    return dt_utc


def get_next_time_slot(workspace_id, user):
    days = {
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
        "Sunday": 7,
    }
    my_times = MyTime.objects.filter(is_active=True, workspace=workspace_id)
    my_time_list = list(my_times.all())

    available_slot_dates = []

    now = datetime.now(timezone.utc)
    today = now.isoweekday()

    week_no = 1

    while not len(available_slot_dates) > 0:
        for time_slot in my_time_list:
            slot_day = time_slot.day
            slot_time = time_slot.time
            slot_day_number = days.get(slot_day)
            day_diff = (
                7 * (week_no - 1) + slot_day_number - today
                if slot_day_number >= today
                else (7 * week_no - today) + slot_day_number
            )
            slot_date = now + timedelta(days=day_diff)
            slot_date_time = datetime.combine(slot_date.date(), slot_time)
            slot_date_time_utc = convert_to_user_timezone(
                user_timezone=user.preference.timezone,
                date_time=slot_date_time,
            )

            post = Post.objects.filter(
                schedule_date_time=slot_date_time_utc,
                workspace=workspace_id,
                status="pending",
            ).first()

            if post is None and slot_date_time_utc > now:
                available_slot_dates.append(slot_date_time_utc)

        week_no += 1

    next_slot = min(available_slot_dates)
    return next_slot
