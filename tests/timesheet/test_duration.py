import datetime

from . import create_timesheet


def test_entry_without_start_time_is_set_previous_start_time():
    contents = """10.10.2012
foo 0900-1000 baz
bar     -1100 bar"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][1].duration == (None, datetime.time(11, 0))


def test_entry_without_start_time_after_entry_without_start_time_has_start_time_set():
    contents = """10.10.2012
foo 0900-1000 baz
bar     -1100 bar
foo     -1300 bar"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][2].duration == (None, datetime.time(13, 0))
