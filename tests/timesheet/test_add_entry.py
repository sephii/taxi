# -*- coding: utf-8 -*-
import datetime

from freezegun import freeze_time
from taxi.timesheet.entry import TimesheetEntry

from . import BaseTimesheetTestCase


class AddEntryTestCase(BaseTimesheetTestCase):
    def test_add_empty_timesheet(self):
        t = self._create_timesheet('')
        today = datetime.date.today()

        entry = TimesheetEntry('foo', 2, 'bar')
        t.entries[today].append(entry)

        entries = t.get_entries()
        self.assertEquals(len(entries), 1)
        self.assertIn(today, entries)
        self.assertIsInstance(entries[today][0], TimesheetEntry)
        self.assertEquals(entries[today][0].alias, 'foo')
        self.assertEquals(entries[today][0].duration, 2)

    @freeze_time('2012-10-13')
    def test_add_entry_empty_end_time(self):
        t = self._create_timesheet('')
        now = datetime.datetime.now()

        entry = TimesheetEntry('foo', (now.time(), None), 'bar')
        t.entries[now.date()].append(entry)

        lines = t.entries.to_lines()
        self.assertEquals(lines, ['13.10.2012', '', 'foo 00:00-? bar'])

    def test_add(self):
        contents = """10.10.2012
foo 09:00-10:00 baz"""

        t = self._create_timesheet(contents)
        t.entries.add_date_to_bottom = True
        e = TimesheetEntry('bar', 2, 'baz')
        t.entries[datetime.date(2012, 10, 10)].append(e)
        e = TimesheetEntry('bar', 2, 'baz')
        t.entries[datetime.date(2012, 10, 20)].append(e)
        entries = t.get_entries()
        self.assertEquals(len(entries), 2)
        self.assertIn(datetime.date(2012, 10, 10), entries)
        self.assertIn(datetime.date(2012, 10, 20), entries)
        self.assertEquals(len(entries[datetime.date(2012, 10, 10)]), 2)
        self.assertEquals(len(entries[datetime.date(2012, 10, 20)]), 1)

        self.assertEquals(t.entries.to_lines(), ['10.10.2012', 'foo 09:00-10:00 baz',
                                         'bar 2 baz', '', '20.10.2012', '',
                                         'bar 2 baz'])

        e = TimesheetEntry('bar', 2, 'baz')
        t.entries.add_date_to_bottom = False
        t.entries[datetime.date(2012, 10, 25)].append(e)

        self.assertEquals(t.entries.to_lines(), ['25.10.2012', '', 'bar 2 baz', '',
                                         '10.10.2012', 'foo 09:00-10:00 baz',
                                         'bar 2 baz', '', '20.10.2012', '',
                                         'bar 2 baz'])

    def test_add_empty_date(self):
        contents = """10.10.2012
"""
        t = self._create_timesheet(contents)
        e = TimesheetEntry('bar', 2, 'baz')
        t.entries[datetime.date(2012, 10, 10)].append(e)

        self.assertEquals(t.entries.to_lines(), [
            '10.10.2012', '', 'bar 2 baz'
        ])
