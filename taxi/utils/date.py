import datetime

def get_previous_working_day(date):
    # Get the number of days required to go to the previous open day (ie. not on
    # a week-end)
    if date.weekday() == 6:
        days = 2
    elif date.weekday() == 0:
        days = 3
    else:
        days = 1

    return date - datetime.timedelta(days=days)
