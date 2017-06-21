from __future__ import unicode_literals

import datetime
import locale
import re

import six


def get_previous_working_day(date):
    # Get the number of days required to go to the previous open day (ie. not
    # on a week-end)
    if date.weekday() == 6:
        days = 2
    elif date.weekday() == 0:
        days = 3
    else:
        days = 1

    return date - datetime.timedelta(days=days)


def unicode_strftime(date, format):
    formatted_date = date.strftime(format)

    if six.PY2:
        locale_encoding = locale.getlocale()[1]
        if locale_encoding is not None:
            formatted_date = formatted_date.decode(locale_encoding)

    return formatted_date


def months_ago(date, nb_months=1):
    """
    Return the given `date` with `nb_months` substracted from it.
    """
    nb_years = nb_months // 12
    nb_months = nb_months % 12

    month_diff = date.month - nb_months

    if month_diff > 0:
        new_month = month_diff
    else:
        new_month = 12 + month_diff
        nb_years += 1

    return date.replace(day=1, month=new_month, year=date.year - nb_years)


def time_ago_to_date(value):
    """
    Parse a date and return it as ``datetime.date`` objects. Examples of valid dates:

        * Relative: 2 days ago, today, yesterday, 1 week ago
        * Absolute: 25.10.2017
    """
    today = datetime.date.today()

    if value == 'today':
        return today
    elif value == 'yesterday':
        return today - datetime.timedelta(days=1)

    time_ago = re.match(r'(\d+) (days?|weeks?|months?|years?) ago', value)

    if time_ago:
        duration, unit = int(time_ago.group(1)), time_ago.group(2)

        if 'day' in unit:
            return today - datetime.timedelta(days=duration)
        elif 'week' in unit:
            return today - datetime.timedelta(weeks=duration)
        elif 'month' in unit:
            return months_ago(today, duration)
        elif 'year' in unit:
            return today.replace(year=today.year - duration)

    return datetime.datetime.strptime(value, '%d.%m.%Y').date()
