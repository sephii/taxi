# -*- coding: utf-8 -*-
import datetime
import unittest

from taxi.parser import DateLine, EntryLine, ParseError, TextLine
from taxi.parser.io import StreamIo
from taxi.parser.parsers.plaintext import PlainTextParser

class TestPlainTextParser(unittest.TestCase):
    def _create_parser(self, text):
        io = StreamIo(text)
        return PlainTextParser(io)

    def test_alias_before_date(self):
        content = """my_alias_1 1 foo bar
11.10.2013
my_alias 2 foo"""

        self.assertRaises(ParseError, self._create_parser, content)

        content = """# comment
11.10.2013
my_alias 2 foo"""

        self.assertIsInstance(self._create_parser(content), PlainTextParser)

    def test_invalid_date(self):
        self.assertRaises(ParseError, self._create_parser, "1110.2013")
        self.assertRaises(ParseError, self._create_parser, "11102013")

    def test_invalid_line(self):
        content = """10.01.2013
foobar 0900-1000 baz
foo"""
        self.assertRaises(ParseError, self._create_parser, content)

    def test_parsing(self):
        contents = """01.01.13

foobar 0900-1000 baz
# comment
foo -1100 bar

2013/09/23
bar 10:00-? ?
foo? 2 foobar"""

        p = self._create_parser(contents)

        self.assertEquals(len(p.parsed_lines), 9)
        self.assertIsInstance(p.parsed_lines[0], DateLine)
        self.assertEquals(p.parsed_lines[0].date, datetime.date(2013, 1, 1))
        self.assertIsInstance(p.parsed_lines[1], TextLine)
        self.assertEquals(p.parsed_lines[1].text, '')
        self.assertIsInstance(p.parsed_lines[2], EntryLine)
        self.assertEquals(p.parsed_lines[2].alias, 'foobar')
        self.assertEquals(p.parsed_lines[2].time,
                          (datetime.time(9, 0), datetime.time(10, 0)))
        self.assertEquals(p.parsed_lines[2].description, 'baz')
        self.assertIsInstance(p.parsed_lines[3], TextLine)
        self.assertEquals(p.parsed_lines[3].text, '# comment')
        self.assertEquals(p.parsed_lines[4].alias, 'foo')
        self.assertEquals(p.parsed_lines[4].time, (None, datetime.time(11, 0)))
        self.assertEquals(p.parsed_lines[4].description, 'bar')
        self.assertIsInstance(p.parsed_lines[6], DateLine)
        self.assertEquals(p.parsed_lines[6].date, datetime.date(2013, 9, 23))
        self.assertIsInstance(p.parsed_lines[7], EntryLine)
        self.assertEquals(p.parsed_lines[7].time, (datetime.time(10, 0), None))
        self.assertIsInstance(p.parsed_lines[8], EntryLine)
        self.assertEquals(p.parsed_lines[8].alias, 'foo?')

    def test_empty(self):
        p = self._create_parser('')

        self.assertEquals(len(p.parsed_lines), 0)

    def test_stripping_empty(self):
        p = self._create_parser("""

""")
        self.assertEquals(len(p.parsed_lines), 0)

    def test_stripping_not_empty(self):
        p = self._create_parser("""

10.01.2013

foobar 0900-1000 baz

""")
        self.assertEquals(len(p.parsed_lines), 3)
