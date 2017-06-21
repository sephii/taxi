import datetime

from taxi.utils.date import months_ago


def test_months_ago_spans_over_year():
    assert months_ago(datetime.date(2017, 1, 15), 1) == datetime.date(2016, 12, 1)


def test_months_ago_spans_over_more_than_1_year():
    assert months_ago(datetime.date(2017, 1, 15), 13) == datetime.date(2015, 12, 1)


def test_months_ago_without_year_span():
    assert months_ago(datetime.date(2017, 2, 15), 1) == datetime.date(2017, 1, 1)
