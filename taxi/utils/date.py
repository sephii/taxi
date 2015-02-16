from __future__ import unicode_literals

import datetime
import locale

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
