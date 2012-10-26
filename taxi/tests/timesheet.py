# -*- coding: utf-8 -*-
import datetime
import unittest

from taxi.exceptions import UndefinedAliasError
from taxi.models import Entry, Timesheet
from taxi.parser import DateLine, EntryLine, ParseError, TextLine
from taxi.parser.io import StreamIo
from taxi.parser.parsers.plaintext import PlainTextParser

class TestTimesheet(unittest.TestCase):
    def _create_timesheet(self, text):
        mappings = {'foo': (123, 456), 'bar': (12, 34)}
        io = StreamIo(text)
        p = PlainTextParser(io)

        return Timesheet(p, mappings, '%d.%m.%Y')

    def test_empty(self):
        t = self._create_timesheet('')
        entries = t.get_entries()
        self.assertEquals(len(entries), 0)

    def test_empty_add(self):
        t = self._create_timesheet('')

        entry = Entry(datetime.date.today(), 'foo', 2, 'bar')
        t.add_entry(entry)

        entries = t.get_entries()
        self.assertEquals(len(entries), 1)
        self.assertIn(datetime.date.today(), entries)
        self.assertIsInstance(entries[datetime.date.today()][0], Entry)
        self.assertEquals(entries[datetime.date.today()][0].project_name, 'foo')
        self.assertEquals(entries[datetime.date.today()][0].duration, 2)

    def test_valid_timesheet(self):
        contents = """10.10.2012
foo 09:00-10:00 baz"""

        t = self._create_timesheet(contents)
        entries = t.get_entries()
        self.assertEquals(len(entries), 1)
        self.assertIn(datetime.date(2012, 10, 10), entries)
        self.assertEquals(len(entries.values()[0]), 1)
        self.assertIsInstance(entries.values()[0][0], Entry)

    def test_to_lines(self):
        contents = """10.10.2012
foo 09:00-10:00 baz
bar -11:00 foobar"""

        t = self._create_timesheet(contents)
        lines = t.to_lines()
        self.assertEquals(len(lines), 3)
        self.assertEquals(lines[0], '10.10.2012')
        self.assertEquals(lines[1], 'foo 09:00-10:00 baz')
        self.assertEquals(lines[2], 'bar -11:00 foobar')

        e = Entry(datetime.date(2012, 9, 29), 'foo', (datetime.time(15, 0), None), 'bar')
        t.add_entry(e)
        lines = t.to_lines()
        self.assertEquals(len(lines), 7)
        self.assertEquals(lines[3], '')
        self.assertEquals(lines[4], '29.09.2012')
        self.assertEquals(lines[5], '')
        self.assertEquals(lines[6], 'foo 15:00-? bar')

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

    def test_undefined_alias(self):
        contents = """10.10.2012
foo 0900-1000 baz"""

        t = self._create_timesheet(contents)
        e = Entry(datetime.date(2012, 10, 21), 'baz', (datetime.time(9, 0),
                  None), 'baz')
        self.assertRaises(UndefinedAliasError, t.add_entry, e)

        lines = t.to_lines()
        self.assertEquals(lines, ['10.10.2012', 'foo 0900-1000 baz'])

    def test_complete_timesheet(self):
        contents = """10.10.2012
foo 0900-1000 baz

11.10.2012
foo 0900-0915 Daily scrum
bar     -1100 Fooing the bar

12.10.2012
foobar? 1200-1300 Baring the foo
foo -1400 Fooed on bar because foo
foo 1400-? ?"""

        t = self._create_timesheet(contents)
        lines = t.to_lines()

        self.assertEquals(lines, [
            "10.10.2012", "foo 0900-1000 baz", "", "11.10.2012",
            "foo 0900-0915 Daily scrum", "bar     -1100 Fooing the bar",
            "", "12.10.2012", "foobar? 1200-1300 Baring the foo",
            "foo -1400 Fooed on bar because foo", "foo 1400-? ?"])

        t.continue_entry(datetime.date(2012, 10, 12), datetime.time(15, 12))
        lines = t.to_lines()

        self.assertEquals(lines[-1], "foo 14:00-15:15 ?")

