# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import pytest

from freezegun import freeze_time

from taxi.timesheet import Timesheet
from taxi.timesheet.entry import (
    AggregatedTimesheetEntry, EntriesCollection, TimesheetEntry,
    UnknownDirectionError
)
from taxi.timesheet.utils import get_files

from . import BaseTimesheetTestCase


class TimesheetTestCase(BaseTimesheetTestCase):
    def test_empty(self):
        t = self._create_timesheet('')
        self.assertEquals(len(t.entries), 0)

    def test_valid_timesheet(self):
        contents = """10.10.2012
foo 09:00-10:00 baz"""

        t = self._create_timesheet(contents)
        self.assertEquals(len(t.entries), 1)
        self.assertIn(datetime.date(2012, 10, 10), t.entries)
        self.assertEquals(len(list(t.entries.values())[0]), 1)
        self.assertIsInstance(list(t.entries.values())[0][0], TimesheetEntry)

    def test_to_lines(self):
        contents = """10.10.2012
foo 09:00-10:00 baz
bar      -11:00 foobar"""

        t = self._create_timesheet(contents, True)
        lines = t.entries.to_lines()
        self.assertEquals(len(lines), 3)
        self.assertEquals(lines[0], '10.10.2012')
        self.assertEquals(lines[1], 'foo 09:00-10:00 baz')
        self.assertEquals(lines[2], 'bar      -11:00 foobar')

        t.entries[datetime.date(2012, 9, 29)].append(
            TimesheetEntry('foo', (datetime.time(15, 0), None), 'bar')
        )
        lines = t.entries.to_lines()
        self.assertEquals(len(lines), 7)
        self.assertEquals(lines[3], '')
        self.assertEquals(lines[4], '29.09.2012')
        self.assertEquals(lines[5], '')
        self.assertEquals(lines[6], 'foo 15:00-? bar')

    def test_undefined_alias(self):
        contents = """10.10.2012
foo 0900-1000 baz"""

        t = self._create_timesheet(contents)
        e = TimesheetEntry('baz', (datetime.time(10, 0), None), 'baz')
        t.entries[datetime.date(2012, 10, 10)].append(e)

        lines = t.entries.to_lines()
        self.assertEquals(lines, [
            '10.10.2012', 'foo 0900-1000 baz', 'baz 10:00-? baz'
        ])

    def test_no_start_time(self):
        contents = """10.10.2012
foo 0900-1000 baz
bar     -1100 bar
foo     -1300 bar"""

        t = self._create_timesheet(contents)
        entries = t.entries
        entries_list = entries[datetime.date(2012, 10, 10)]
        self.assertEquals(len(entries_list), 3)
        self.assertEquals(entries_list[0].duration, (datetime.time(9, 0),
                                                     datetime.time(10, 0)))
        self.assertEquals(entries_list[0].hours, 1)
        self.assertEquals(entries_list[1].duration, (None,
                                                     datetime.time(11, 0)))
        self.assertEquals(entries_list[1].hours, 1)
        self.assertEquals(entries_list[2].duration, (None,
                                                     datetime.time(13, 0)))
        self.assertEquals(entries_list[2].hours, 2)

        contents = """10.10.2012
foo 0900-1000 baz
bar 2 bar
foo     -1200 bar"""
        t = self._create_timesheet(contents)
        self.assertTrue(t.entries[datetime.date(2012, 10, 10)][2].is_ignored())

        contents = """10.10.2012
foo -1000 baz"""
        t = self._create_timesheet(contents)
        self.assertTrue(t.entries[datetime.date(2012, 10, 10)][0].is_ignored())

        contents = """10.10.2012
foo 0900-1000 baz
bar 1000-? bar
foo     -1200 bar"""
        t = self._create_timesheet(contents)
        self.assertTrue(t.entries[datetime.date(2012, 10, 10)][2].is_ignored())

    def test_complete_timesheet(self):
        contents = """10.10.2012
foo 0900-1000 baz

11.10.2012
foo 0900-0915 Daily scrum
bar     -1100 Fooing the bar

12.10.2012
foobar? 1200-1300 Baring the foo
foo         -1400 Fooed on bar because foo
foo     0         Ignored foobar
foo     1400-?    ?"""

        t = self._create_timesheet(contents)
        lines = t.entries.to_lines()

        self.assertEquals(lines, [
            u"10.10.2012", u"foo 0900-1000 baz", u"", u"11.10.2012",
            u"foo 0900-0915 Daily scrum", u"bar     -1100 Fooing the bar",
            u"", "12.10.2012", u"foobar? 1200-1300 Baring the foo",
            u"foo         -1400 Fooed on bar because foo", u"foo     0         Ignored foobar",
            u"foo     1400-?    ?"])

        ignored_entries = t.get_ignored_entries()
        self.assertEquals(len(ignored_entries), 3)
        self.assertEquals(len(ignored_entries[datetime.date(2012, 10, 12)]), 3)

        t.continue_entry(datetime.date(2012, 10, 12), datetime.time(15, 12))

        lines = t.entries.to_lines()
        self.assertEquals(lines[-1], "foo     1400-1515 ?")

        entries = t.get_entries(datetime.date(2012, 10, 12))
        self.assertEquals(len(entries), 1)
        entries_list = entries[datetime.date(2012, 10, 12)]
        self.assertEquals(len(entries_list), 4)
        self.assertEquals(entries_list[0].alias, 'foobar')
        self.assertTrue(entries_list[0].is_ignored())
        self.assertEquals(entries_list[0].duration, (datetime.time(12, 0),
                                                     datetime.time(13, 0)))
        self.assertEquals(entries_list[1].alias, 'foo')
        self.assertFalse(entries_list[1].is_ignored())
        self.assertTrue(entries_list[2].is_ignored())
        self.assertEquals(entries_list[2].duration, 0)
        self.assertFalse(entries_list[3].is_ignored())
        self.assertEquals(entries_list[3].duration,
                          (datetime.time(14, 0), datetime.time(15, 15)))

    def test_is_top_down(self):
        contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar"""

        t = self._create_timesheet(contents)
        with pytest.raises(UnknownDirectionError):
            t.entries.is_top_down()

        contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        with pytest.raises(UnknownDirectionError):
            t.entries.is_top_down()

        contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar
01.04.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        self.assertTrue(t.entries.is_top_down())

        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        self.assertFalse(t.entries.is_top_down())

        contents = """01.04.2013
31.03.2013"""

        t = self._create_timesheet(contents)
        self.assertFalse(t.entries.is_top_down())

    def test_comment_entries(self):
        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        entries = t.get_entries(datetime.date(2013, 4, 1))

        for entry in list(entries.values())[0]:
            entry.commented = True

        lines = t.entries.to_lines()
        self.assertEquals(lines, [
            "01.04.2013", "# foo 2 bar", "# bar 0900-1000 bar", "31.03.2013",
            "foo 1 bar"
        ])

    def test_add_date(self):
        t = self._create_timesheet('', add_date_to_bottom=True)
        t.entries[datetime.date(2013, 1, 1)] = []
        t.entries[datetime.date(2013, 1, 2)] = []

        lines = t.entries.to_lines()
        self.assertEquals(lines, ["01.01.2013", "", "02.01.2013"])

        t = self._create_timesheet('', add_date_to_bottom=False)
        t.entries[datetime.date(2013, 1, 1)] = []
        t.entries[datetime.date(2013, 1, 2)] = []

        lines = t.entries.to_lines()
        self.assertEquals(lines, ["02.01.2013", "", "01.01.2013"])

    def test_regroup(self):
        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
foo 2 bar
foo 3 bar
foo 1 barz"""

        t = self._create_timesheet(contents)
        entries = t.get_entries(regroup=True)[datetime.date(2013, 4, 1)]
        self.assertEquals(len(entries), 3)
        self.assertEquals(entries[0].hours, 7)
        self.assertIsInstance(entries[0], AggregatedTimesheetEntry)
        self.assertEquals(len(entries[0].entries), 3)
        for entry in entries[0].entries:
            self.assertIsInstance(entry, TimesheetEntry)

    def test_regroup_partial_time(self):
        contents = """01.04.2013
foo 2 bar
foo 0800-0900 bar
bar -1000 bar
foo -1100 bar"""
        t = self._create_timesheet(contents)
        entries = t.get_entries(regroup=True)[datetime.date(2013, 4, 1)]
        self.assertEquals(len(entries), 2)
        self.assertEquals(entries[0].hours, 4)

    def test_comment_regrouped_entries(self):
        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
foo 1 bar"""
        t = self._create_timesheet(contents)
        entries = t.get_entries(regroup=True)[datetime.date(2013, 4, 1)]
        for entry in entries:
            entry.commented = True
        lines = t.entries.to_lines()
        self.assertEquals(lines, ["01.04.2013", "# foo 2 bar",
                                  "# bar 0900-1000 bar", "# foo 1 bar"])


def test_empty_timesheet():
    timesheet = Timesheet()
    assert len(timesheet.entries) == 0


def test_timesheet_with_entries():
    entries = EntriesCollection("""10.10.2014\nfoo 2 bar\n11.10.2014\nfoo 1 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.entries) == 2


def test_get_entries():
    entries = EntriesCollection("""10.10.2014\nfoo 2 bar\n11.10.2014\nfoo 1 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.get_entries(datetime.date(2014, 10, 10))) == 1


@freeze_time('2014-01-02')
def test_current_workday_entries():
    entries = EntriesCollection("""01.01.2014\nfoo 2 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.get_non_current_workday_entries()) == 0


@freeze_time('2014-01-03')
def test_non_current_workday_entries():
    entries = EntriesCollection("""01.01.2014\nfoo 2 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.get_non_current_workday_entries()) == 1


def test_non_current_workday_entries_ignored():
    entries = EntriesCollection("""04.01.2014\nfoo? 2 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.get_non_current_workday_entries()) == 0


def test_get_files_m_returns_previous_files():
    f = get_files('foo_%m', 2, datetime.date(2014, 3, 1))
    assert f == ['foo_03', 'foo_02', 'foo_01']


def test_get_files_m_spans_over_previous_year():
    f = get_files('foo_%m', 2, datetime.date(2014, 2, 1))
    assert f == ['foo_02', 'foo_01', 'foo_12']


def test_get_files_m_spans_over_previous_year_and_changes_year():
    f = get_files('foo_%m_%Y', 2, datetime.date(2014, 2, 1))
    assert f == ['foo_02_2014', 'foo_01_2014', 'foo_12_2013']


def test_get_files_Y_returns_previous_files():
    f = get_files('foo_%Y', 2, datetime.date(2014, 2, 1))
    assert f == ['foo_2014', 'foo_2013', 'foo_2012']
