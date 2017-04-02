import datetime

from . import create_timesheet


def test_is_top_down_with_single_date_returns_none():
    contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar"""

    t = create_timesheet(contents)
    assert t.entries.is_top_down() is None


def test_is_top_down_returns_true_for_top_down_dates():
    contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar
01.04.2013
foo 1 bar"""

    t = create_timesheet(contents)
    assert t.entries.is_top_down()


def test_is_top_down_returns_false_for_down_top_dates():
    contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

    t = create_timesheet(contents)
    assert not t.entries.is_top_down()


def test_is_top_down_returns_false_for_down_top_dates_without_entries():
    contents = """01.04.2013
31.03.2013"""

    t = create_timesheet(contents)
    assert not t.entries.is_top_down()


def test_add_date_with_add_date_to_bottom_adds_date_to_bottom():
    t = create_timesheet('', add_date_to_bottom=True)
    t.entries[datetime.date(2013, 1, 1)] = []
    t.entries[datetime.date(2013, 1, 2)] = []

    assert t.entries.to_lines() == ["01.01.2013", "", "02.01.2013"]


def test_add_date_without_add_date_to_bottom_adds_date_to_top():
    t = create_timesheet('', add_date_to_bottom=False)
    t.entries[datetime.date(2013, 1, 1)] = []
    t.entries[datetime.date(2013, 1, 2)] = []

    assert t.entries.to_lines() == ["02.01.2013", "", "01.01.2013"]
