# -*- coding: utf-8 -*-
import datetime
import unittest

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
        contents = """10.10.2012
foo 09:00-10:00 baz"""

        t = self._create_timesheet(contents)
        entries = t.get_entries()
        self.assertEquals(len(entries), 2)
        self.assertEquals(entries[0], datetime.date(2012, 10, 10))
        self.assertIsInstance(entries[1], Entry)
        lines = t.to_lines()
        self.assertEquals(len(lines), 2)
        self.assertEquals(lines[0], '10.10.2012')
        self.assertEquals(lines[1], 'foo 09:00-10:00 baz')
        e = Entry(datetime.date(2012, 10, 10), 'bar', 2, 'baz')
        #>>> t.add_entry(e)
        #>>> t.get_entries() # doctest: +ELLIPSIS
        #[(datetime.date(2012, 10, 10), [<models.Entry instance at 0x...>, <models.Entry instance at 0x...])]
        #>>> t.to_lines()
        #['10.10.2012', 'foo 09:00-10:00 baz', 'bar 2 baz']
        #>>> e = Entry(datetime.date(2012, 10, 21), 'baz', (datetime.time(9, 0),
        #... None), 'baz')
        #>>> t.add_entry(e)
        #Traceback (most recent call last):
        #...
        #UndefinedAliasError: baz
        #>>> t.to_lines()
        #['10.10.2012', 'foo 09:00-10:00 baz', 'bar 2 baz']
        pass
