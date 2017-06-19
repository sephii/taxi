# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import unittest

from freezegun import freeze_time

from taxi.timesheet import Entry

from . import create_timesheet


class AddEntryTestCase(unittest.TestCase):
    def test_add_empty_timesheet(self):
        t = create_timesheet('')
        today = datetime.date.today()

        entry = Entry('foo', 2, 'bar')
        t.entries[today].append(entry)

        entries = t.entries
        self.assertEquals(len(entries), 1)
        self.assertIn(today, entries)
        self.assertIsInstance(entries[today][0], Entry)
        self.assertEquals(entries[today][0].alias, 'foo')
        self.assertEquals(entries[today][0].duration, 2)

    @freeze_time('2012-10-13')
    def test_add_entry_empty_end_time(self):
        t = create_timesheet('')
        now = datetime.datetime.now()

        entry = Entry('foo', (now.time(), None), 'bar')
        t.entries[now.date()].append(entry)

        lines = t.entries.to_lines()
        self.assertEquals(lines, ['13.10.2012', '', 'foo 00:00-? bar'])

    def test_add(self):
        contents = """10.10.2012
foo 09:00-10:00 baz"""

        t = create_timesheet(contents)
        t.entries.parser.add_date_to_bottom = True
        e = Entry('bar', 2, 'baz')
        t.entries[datetime.date(2012, 10, 10)].append(e)
        e = Entry('bar', 2, 'baz')
        t.entries[datetime.date(2012, 10, 20)].append(e)
        entries = t.entries
        self.assertEquals(len(entries), 2)
        self.assertIn(datetime.date(2012, 10, 10), entries)
        self.assertIn(datetime.date(2012, 10, 20), entries)
        self.assertEquals(len(entries[datetime.date(2012, 10, 10)]), 2)
        self.assertEquals(len(entries[datetime.date(2012, 10, 20)]), 1)

        self.assertEquals(t.entries.to_lines(), ['10.10.2012', 'foo 09:00-10:00 baz',
                                         'bar 2 baz', '', '20.10.2012', '',
                                         'bar 2 baz'])

        e = Entry('bar', 2, 'baz')
        t.entries.parser.add_date_to_bottom = False
        t.entries[datetime.date(2012, 10, 25)].append(e)

        self.assertEquals(t.entries.to_lines(), ['25.10.2012', '', 'bar 2 baz', '',
                                         '10.10.2012', 'foo 09:00-10:00 baz',
                                         'bar 2 baz', '', '20.10.2012', '',
                                         'bar 2 baz'])

    def test_add_empty_date(self):
        contents = """10.10.2012
"""
        t = create_timesheet(contents)
        e = Entry('bar', 2, 'baz')
        t.entries[datetime.date(2012, 10, 10)].append(e)

        self.assertEquals(t.entries.to_lines(), [
            '10.10.2012', '', 'bar 2 baz'
        ])
