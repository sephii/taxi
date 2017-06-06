import datetime

from taxi.timesheet import TimesheetCollection


def test_get_files_m_returns_previous_files():
    f = TimesheetCollection.get_files('foo_%m', 2, datetime.date(2014, 3, 1))
    assert f == ['foo_03', 'foo_02', 'foo_01']


def test_get_files_m_spans_over_previous_year():
    f = TimesheetCollection.get_files('foo_%m', 2, datetime.date(2014, 2, 1))
    assert f == ['foo_02', 'foo_01', 'foo_12']


def test_get_files_m_spans_over_previous_year_and_changes_year():
    f = TimesheetCollection.get_files('foo_%m_%Y', 2, datetime.date(2014, 2, 1))
    assert f == ['foo_02_2014', 'foo_01_2014', 'foo_12_2013']


def test_get_files_Y_returns_previous_files():
    f = TimesheetCollection.get_files('foo_%Y', 2, datetime.date(2014, 2, 1))
    assert f == ['foo_2014', 'foo_2013', 'foo_2012']
