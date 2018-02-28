# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from freezegun import freeze_time

from taxi.timesheet import EntriesCollection, Entry, Timesheet, TimesheetParser

from . import create_timesheet


def test_empty_timesheet_has_zero_entries():
    t = create_timesheet('')
    assert len(t.entries) == 0


def test_entry_alias_is_extracted():
    contents = """10.10.2012
foo 09:00-10:00 baz"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].alias == 'foo'


def test_entry_description_is_extracted():
    contents = """10.10.2012
foo 09:00-10:00 baz"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].description == 'baz'


def test_entry_start_and_end_time_are_extracted():
    contents = """10.10.2012
foo 09:00-10:00 baz"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].duration == (datetime.time(9), datetime.time(10))


def test_entry_duration_is_extracted():
    contents = """10.10.2012
foo 1.25 baz"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].duration == 1.25


def test_entry_duration_looking_like_start_time_is_extracted():
    contents = """10.10.2012
foo 100 baz"""

    t = create_timesheet(contents)
    assert list(t.entries.values())[0][0].duration == 100


def test_entry_with_undefined_alias_can_be_added():
    contents = """10.10.2012
foo 0900-1000 baz"""

    t = create_timesheet(contents)
    e = Entry('baz', (datetime.time(10, 0), None), 'baz')
    t.entries[datetime.date(2012, 10, 10)].append(e)

    lines = t.entries.to_lines()
    assert lines == [
        '10.10.2012', 'foo 0900-1000 baz', 'baz 10:00-? baz'
    ]


def test_empty_timesheet():
    timesheet = Timesheet()
    assert len(timesheet.entries) == 0


def test_timesheet_with_entries():
    entries = EntriesCollection(TimesheetParser(), """10.10.2014\nfoo 2 bar\n11.10.2014\nfoo 1 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.entries) == 2


def test_get_entries():
    entries = EntriesCollection(TimesheetParser(), """10.10.2014\nfoo 2 bar\n11.10.2014\nfoo 1 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.entries.filter(date=datetime.date(2014, 10, 10))) == 1


@freeze_time('2014-01-02')
def test_current_workday_entries():
    entries = EntriesCollection(TimesheetParser(), """01.01.2014\nfoo 2 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.entries.filter(current_workday=False)) == 0


@freeze_time('2014-01-03')
def test_non_current_workday_entries():
    entries = EntriesCollection(TimesheetParser(), """01.01.2014\nfoo 2 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.entries.filter(current_workday=False)) == 1


def test_continuation_with_previous_entry_pushed():
    contents = """03.07.2017
= alias_1       0845-0930 xxx
alias_1       -1000 xxx
"""
    timesheet = create_timesheet(contents)
    continuation_entry = timesheet.entries[datetime.date(2017, 7, 3)][1]

    assert continuation_entry.duration == (None, datetime.time(10))
    assert continuation_entry.hours == 0.5
