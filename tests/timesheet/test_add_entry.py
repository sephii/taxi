# -*- coding: utf-8 -*-
import datetime

from freezegun import freeze_time
from taxi.models import Entry

from . import BaseTimesheetTestCase


class AddEntryTestCase(BaseTimesheetTestCase):
    def test_add_empty_timesheet(self):
        t = self._create_timesheet('')

        entry = Entry(datetime.date.today(), 'foo', 2, 'bar')
        t.add_entry(entry)

        entries = t.get_entries()
        self.assertEquals(len(entries), 1)
        self.assertIn(datetime.date.today(), entries)
        self.assertIsInstance(entries[datetime.date.today()][0], Entry)
        self.assertEquals(entries[datetime.date.today()][0].project_name, 'foo')
        self.assertEquals(entries[datetime.date.today()][0].duration, 2)

    @freeze_time('2012-10-13')
    def test_add_entry_empty_end_time(self):
        t = self._create_timesheet('')

        entry = Entry(datetime.date.today(), 'foo',
                      (datetime.datetime.now(), None), 'bar')
        t.add_entry(entry)

        lines = t.to_lines()
        self.assertEquals(lines, ['13.10.2012', '', 'foo 00:00-? bar'])

    def test_add(self):
        contents = """10.10.2012
foo 09:00-10:00 baz"""

        t = self._create_timesheet(contents)
        e = Entry(datetime.date(2012, 10, 10), 'bar', 2, 'baz')
        t.add_entry(e)
        e = Entry(datetime.date(2012, 10, 20), 'bar', 2, 'baz')
        t.add_entry(e)
        entries = t.get_entries()
        self.assertEquals(len(entries), 2)
        self.assertIn(datetime.date(2012, 10, 10), entries)
        self.assertIn(datetime.date(2012, 10, 20), entries)
        self.assertEquals(len(entries[datetime.date(2012, 10, 10)]), 2)
        self.assertEquals(len(entries[datetime.date(2012, 10, 20)]), 1)

        self.assertEquals(t.to_lines(), ['10.10.2012', 'foo 09:00-10:00 baz',
                                         'bar 2 baz', '', '20.10.2012', '',
                                         'bar 2 baz'])

        e = Entry(datetime.date(2012, 10, 25), 'bar', 2, 'baz')
        t.add_entry(e, add_to_bottom=False)

        self.assertEquals(t.to_lines(), ['25.10.2012', '', 'bar 2 baz', '',
                                         '10.10.2012', 'foo 09:00-10:00 baz',
                                         'bar 2 baz', '', '20.10.2012', '',
                                         'bar 2 baz'])

    def test_add_empty_date(self):
        contents = """10.10.2012
"""
        t = self._create_timesheet(contents)
        e = Entry(datetime.date(2012, 10, 10), 'bar', 2, 'baz')
        t.add_entry(e)
