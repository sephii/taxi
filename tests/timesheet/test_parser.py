import datetime
import pytest
import unittest

from taxi.timesheet.parser import (
    DateLine, EntryLine, ParseError, TextLine, TimesheetParser
)


def test_extract_date_dot_separator():
    assert TimesheetParser.extract_date('1.1.2010') == datetime.date(2010, 1, 1)


def test_extract_date_slash_separator():
    assert TimesheetParser.extract_date('05/08/2012') == datetime.date(2012, 8, 5)


def test_extract_date_short_year():
    assert TimesheetParser.extract_date('05/08/12') == datetime.date(2012, 8, 5)


def test_extract_date_yyyy_mm_dd():
    assert TimesheetParser.extract_date('2013/08/09') == datetime.date(2013, 8, 9)


def test_extract_date_invalid_string():
    with pytest.raises(ValueError):
        assert TimesheetParser.extract_date('foobar')


def test_extract_date_incomplete_date():
    with pytest.raises(ValueError):
        assert TimesheetParser.extract_date('05/08')


def test_extract_date_missing_separator():
    with pytest.raises(ValueError):
        assert TimesheetParser.extract_date('05.082012')


def test_extract_date_missing_all_separators():
    with pytest.raises(ValueError):
        assert TimesheetParser.extract_date('05082012')


def test_extract_date_yyyy_mm_dd_missing_separator():
    with pytest.raises(ValueError):
        assert TimesheetParser.extract_date('2012/0801')


def test_parse_time_valid_decimal():
    assert TimesheetParser.parse_time('1.75') == 1.75


def test_parse_time_valid_integer():
    TimesheetParser.parse_time('3') == 3.0


def test_parse_time_valid_big_integer():
    TimesheetParser.parse_time('0900') == 900.0


def test_parse_time_valid_timespan():
    TimesheetParser.parse_time('0900-1015') == (datetime.time(9, 0), datetime.time(10, 15))


def test_parse_time_valid_timespan_with_separators():
    TimesheetParser.parse_time('09:00-10:15') == (datetime.time(9, 0), datetime.time(10, 15))

def test_parse_time_valid_timespan_without_end():
    TimesheetParser.parse_time('09:00-?') == (datetime.time(9, 0), None)


def test_parse_time_valid_timespan_without_start():
    TimesheetParser.parse_time('-10:15') == (None, datetime.time(10, 15))


def test_parse_time_invalid_string():
    with pytest.raises(ParseError):
        TimesheetParser.parse_time('foo')


def test_parse_time_hours_out_of_range():
    with pytest.raises(ParseError):
        TimesheetParser.parse_time('-2500')


def test_parse_time_minutes_out_of_range():
    with pytest.raises(ParseError):
        TimesheetParser.parse_time('-1061')

def test_parse_time_separator_without_timespan():
    with pytest.raises(ParseError):
        TimesheetParser.parse_time('-')


class TestPlainTextParser(unittest.TestCase):
    def test_alias_before_date(self):
        content = """my_alias_1 1 foo bar
11.10.2013
my_alias 2 foo"""

        with pytest.raises(ParseError):
            TimesheetParser.parse(content)

        content = """# comment
11.10.2013
my_alias 2 foo"""

        lines = TimesheetParser.parse(content)
        self.assertEqual(len(lines), 3)

    def test_invalid_date(self):
        with pytest.raises(ParseError):
            TimesheetParser.parse("1110.2013")
            TimesheetParser.parse("11102013")

    def test_invalid_line(self):
        content = """10.01.2013
foobar 0900-1000 baz
foo"""
        with pytest.raises(ParseError):
            TimesheetParser.parse(content)

    def test_parsing(self):
        contents = """01.01.13

foobar 0900-1000 baz
# comment
foo -1100 bar

2013/09/23
bar 10:00-? ?
foo? 2 foobar"""

        lines = TimesheetParser.parse(contents)

        self.assertEquals(len(lines), 9)
        self.assertIsInstance(lines[0], DateLine)
        self.assertEquals(lines[0].date, datetime.date(2013, 1, 1))
        self.assertIsInstance(lines[1], TextLine)
        self.assertEquals(lines[1].text, '')
        self.assertIsInstance(lines[2], EntryLine)
        self.assertEquals(lines[2].alias, 'foobar')
        self.assertEquals(lines[2].duration,
                          (datetime.time(9, 0), datetime.time(10, 0)))
        self.assertEquals(lines[2].description, 'baz')
        self.assertIsInstance(lines[3], TextLine)
        self.assertEquals(lines[3].text, '# comment')
        self.assertEquals(lines[4].alias, 'foo')
        self.assertEquals(lines[4].duration, (None, datetime.time(11, 0)))
        self.assertEquals(lines[4].description, 'bar')
        self.assertIsInstance(lines[6], DateLine)
        self.assertEquals(lines[6].date, datetime.date(2013, 9, 23))
        self.assertIsInstance(lines[7], EntryLine)
        self.assertEquals(lines[7].duration, (datetime.time(10, 0), None))
        self.assertIsInstance(lines[8], EntryLine)
        self.assertEquals(lines[8].alias, 'foo')
        self.assertTrue(lines[8].ignored)

    def test_empty(self):
        self.assertEquals(len(TimesheetParser.parse('')), 0)

    def test_stripping_empty(self):
        lines = TimesheetParser.parse("""

""")
        self.assertEquals(len(lines), 0)

    def test_stripping_not_empty(self):
        lines = TimesheetParser.parse("""

10.01.2013

foobar 0900-1000 baz

""")
        self.assertEquals(len(lines), 3)
