# -*- coding: utf-8 -*-
import datetime
import unittest

from taxi.exceptions import UndefinedAliasError, UnknownDirectionError
from taxi.models import Entry, AggregatedEntry, Timesheet
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

    def test_no_start_time(self):
        contents = """10.10.2012
foo 0900-1000 baz
bar     -1100 bar
foo     -1200 bar"""

        t = self._create_timesheet(contents)
        entries = t.get_entries()
        entries_list = entries[datetime.date(2012, 10, 10)]
        self.assertEquals(len(entries_list), 3)
        self.assertEquals(entries_list[0].duration, (datetime.time(9, 0),
                                                     datetime.time(10, 0)))
        self.assertEquals(entries_list[1].duration, (datetime.time(10, 0),
                                                     datetime.time(11, 0)))
        self.assertEquals(entries_list[2].duration, (datetime.time(11, 0),
                                                     datetime.time(12, 0)))

        contents = """10.10.2012
foo 0900-1000 baz
bar 2 bar
foo     -1200 bar"""
        self.assertRaises(ParseError, self._create_timesheet, contents)

        contents = """10.10.2012
foo -1000 baz"""
        self.assertRaises(ParseError, self._create_timesheet, contents)

        contents = """10.10.2012
foo 0900-1000 baz
bar 1000-? bar
foo     -1200 bar"""
        self.assertRaises(ParseError, self._create_timesheet, contents)

    def test_complete_timesheet(self):
        contents = """10.10.2012
foo 0900-1000 baz

11.10.2012
foo 0900-0915 Daily scrum
bar     -1100 Fooing the bar

12.10.2012
foobar? 1200-1300 Baring the foo
foo -1400 Fooed on bar because foo
foo 0 Ignored foobar
foo 1400-? ?"""

        t = self._create_timesheet(contents)
        lines = t.to_lines()

        self.assertEquals(lines, [
            "10.10.2012", "foo 0900-1000 baz", "", "11.10.2012",
            "foo 0900-0915 Daily scrum", "bar     -1100 Fooing the bar",
            "", "12.10.2012", "foobar? 1200-1300 Baring the foo",
            "foo -1400 Fooed on bar because foo", "foo 0 Ignored foobar",
            "foo 1400-? ?"])

        ignored_entries = t.get_ignored_entries()
        self.assertEquals(len(ignored_entries), 1)
        self.assertEquals(len(ignored_entries[datetime.date(2012, 10, 12)]), 3)

        t.continue_entry(datetime.date(2012, 10, 12), datetime.time(15, 12))

        lines = t.to_lines()
        self.assertEquals(lines[-1], "foo 14:00-15:15 ?")

        entries = t.get_entries(datetime.date(2012, 10, 12))
        self.assertEquals(len(entries), 1)
        entries_list = entries[datetime.date(2012, 10, 12)]
        self.assertEquals(len(entries_list), 4)
        self.assertEquals(entries_list[0].project_name, 'foobar')
        self.assertTrue(entries_list[0].is_ignored())
        self.assertEquals(entries_list[0].duration, (datetime.time(12, 0),
                                                     datetime.time(13, 0)))
        self.assertEquals(entries_list[1].project_name, 'foo')
        self.assertFalse(entries_list[1].is_ignored())
        self.assertTrue(entries_list[2].is_ignored())
        self.assertEquals(entries_list[2].duration, 0)
        self.assertTrue(entries_list[3].is_ignored())
        self.assertEquals(entries_list[3].duration, (datetime.time(14, 0), None))

    def test_is_top_down(self):
        contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar"""

        t = self._create_timesheet(contents)
        self.assertRaises(UnknownDirectionError, t.is_top_down)

        contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        self.assertRaises(UnknownDirectionError, t.is_top_down)

        contents = """31.03.2013
foo 2 bar
bar 0900-1000 bar
01.04.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        self.assertTrue(t.is_top_down())

        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        self.assertFalse(t.is_top_down())

        contents = """01.04.2013
31.03.2013"""

        t = self._create_timesheet(contents)
        self.assertFalse(t.is_top_down())

    def test_comment_entries(self):
        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
31.03.2013
foo 1 bar"""

        t = self._create_timesheet(contents)
        entries = t.get_entries(datetime.date(2013, 4, 1))

        for (date, entries_list) in entries.iteritems():
            t.comment_entries(entries_list)

        entries = t.get_entries()
        self.assertEquals(entries[datetime.date(2013, 4, 1)], [])
        self.assertEquals(len(entries[datetime.date(2013, 3, 31)]), 1)

        lines = t.to_lines()
        self.assertEquals(lines, ["01.04.2013", "# foo 2 bar",
                                  "# bar 0900-1000 bar", "31.03.2013",
                                  "foo 1 bar"])

    def test_add_date(self):
        t = self._create_timesheet('')
        t.add_date(datetime.date(2013, 1, 1))
        self.assertEquals(len(t.get_entries()), 1)
        t.add_date(datetime.date(2013, 1, 1))
        self.assertEquals(len(t.get_entries()), 1)
        t.add_date(datetime.date(2013, 1, 2))
        self.assertEquals(len(t.get_entries()), 2)

        lines = t.to_lines()
        self.assertEquals(lines, ["", "01.01.2013", "", "02.01.2013", ""])

        t = self._create_timesheet('')
        t.add_date(datetime.date(2013, 1, 1), False)
        t.add_date(datetime.date(2013, 1, 2), False)

        lines = t.to_lines()
        self.assertEquals(lines, ["02.01.2013", "", "01.01.2013", "", ""])

    def test_regroup(self):
        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
foo 2 bar
foo 1 barz"""

        t = self._create_timesheet(contents)
        entries = t.get_entries(regroup=True)[datetime.date(2013, 4, 1)]
        self.assertEquals(len(entries), 3)
        self.assertEquals(entries[0].duration, 4)
        self.assertIsInstance(entries[0], AggregatedEntry)

    def test_regroup_partial_time(self):
        contents = """01.04.2013
foo 2 bar
foo 0800-0900 bar
bar -1000 bar
foo -1100 bar"""
        t = self._create_timesheet(contents)
        entries = t.get_entries(regroup=True)[datetime.date(2013, 4, 1)]
        self.assertEquals(len(entries), 2)
        self.assertEquals(entries[0].duration, 4)

    def test_comment_regrouped_entries(self):
        contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
foo 1 bar"""
        t = self._create_timesheet(contents)
        entries = t.get_entries(regroup=True)[datetime.date(2013, 4, 1)]
        t.comment_entries(entries)
        lines = t.to_lines()
        self.assertEquals(lines, ["01.04.2013", "# foo 2 bar",
                                  "# bar 0900-1000 bar", "# foo 1 bar"])
