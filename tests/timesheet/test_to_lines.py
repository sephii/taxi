import datetime

from taxi.timesheet import Entry

from . import create_timesheet


def test_to_lines_returns_all_lines():
    contents = """10.10.2012
foo 09:00-10:00 baz
bar      -11:00 foobar"""

    t = create_timesheet(contents, True)
    lines = t.entries.to_lines()
    assert lines == ['10.10.2012', 'foo 09:00-10:00 baz',
                     'bar      -11:00 foobar']


def test_to_lines_returns_appended_lines():
    contents = """10.10.2012
foo 09:00-10:00 baz
bar      -11:00 foobar"""

    t = create_timesheet(contents, True)
    t.entries[datetime.date(2012, 9, 29)].append(
        Entry('foo', (datetime.time(15, 0), None), 'bar')
    )
    lines = t.entries.to_lines()
    assert lines == ['10.10.2012', 'foo 09:00-10:00 baz',
                     'bar      -11:00 foobar', '', '29.09.2012', '',
                     'foo 15:00-? bar']


def test_to_lines_reports_push_flag():
    contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

    t = create_timesheet(contents)
    entries = t.entries.filter(date=datetime.date(2013, 4, 1))

    for entry in list(entries.values())[0]:
        entry.pushed = True

    assert t.entries.to_lines() == [
        "01.04.2013", "= foo 2 bar", "= bar 0900-1000 bar", "31.03.2013",
        "foo 1 bar"
    ]
