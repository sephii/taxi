import datetime

from freezegun import freeze_time

from taxi.commands.types import Date


def get_date(date):
    return Date().convert(date, None, None)


def test_date_today():
    assert get_date('today') == datetime.date.today()


def test_date_yesterday():
    assert get_date('yesterday') == datetime.date.today() - datetime.timedelta(days=1)


def test_date_weeks_ago():
    assert get_date('2 weeks ago') == datetime.date.today() - datetime.timedelta(days=14)


@freeze_time('2017-06-20')
def test_date_months_ago():
    assert get_date('2 months ago') == datetime.date(2017, 4, 1)


def test_date_days_ago():
    assert get_date('7 days ago') == datetime.date.today() - datetime.timedelta(days=7)


def test_absolute_date():
    assert get_date('25.07.2016') == datetime.date(2016, 7, 25)
