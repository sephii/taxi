# -*- coding: utf-8 -*-

import datetime
import re

from taxi.parser import DateLine, EntryLine, ParseError, TextLine
from taxi.parser.parsers import BaseParser

class PlainTextParser(BaseParser):
    r"""
    >>> from taxi.parser.io import StreamIo
    >>> sr = StreamIo("01.01.2013\n\nfoobar 0900-1000 baz\n# comment\nfoo -1100 bar")
    >>> t = PlainTextParser(sr)
    ...
    >>> len(t.parsed_lines)
    5
    >>> type(t.parsed_lines[0])
    <class 'taxi.parser.DateLine'>
    >>> t.parsed_lines[0].date
    datetime.date(2013, 1, 1)
    >>> type(t.parsed_lines[1])
    <class 'taxi.parser.TextLine'>
    >>> t.parsed_lines[1].text
    ''
    >>> type(t.parsed_lines[2])
    <class 'taxi.parser.EntryLine'>
    >>> t.parsed_lines[2].alias
    'foobar'
    >>> t.parsed_lines[2].time
    (datetime.time(9, 0), datetime.time(10, 0))
    >>> t.parsed_lines[2].description
    'baz'
    >>> type(t.parsed_lines[3])
    <class 'taxi.parser.TextLine'>
    >>> t.parsed_lines[3].text
    '# comment'
    >>> t.parsed_lines[4].alias
    'foo'
    >>> t.parsed_lines[4].time
    (None, datetime.time(11, 0))
    >>> t.parsed_lines[4].description
    'bar'
    >>> sr = StreamIo("01.01.2013\n\nfoobar 0u900-1000 baz\n# comment\nfoo -1100 bar")
    >>> t = PlainTextParser(sr)
    Traceback (most recent call last):
        ...
    ParseError: Parse error at line 3: The duration must be a float number or a HH:mm string
    """

    def __init__(self, file):
        self.current_date = None
        super(PlainTextParser, self).__init__(file)

    def parse_line(self):
        line = self._get_current_line().strip()

        if len(line) == 0 or line[0] == '#':
            return TextLine(line)

        date = self.extract_date(line)

        if date is not None:
            self.current_date = date

            return DateLine(date, line)
        else:
            if self.current_date is None:
                raise ParseError("Entries must be defined inside a date "
                                 "section")

            return self._parse_entry_line(line)

    def _parse_entry_line(self, line):
        split_line = line.split(None, 2)

        if len(split_line) != 3:
            raise ParseError("Couldn't split line into 3 chunks")

        alias = self._process_alias(split_line[0])
        time = self._process_time(split_line[1])
        description = self._process_description(split_line[2])

        return EntryLine(alias, time, description, line)

    def _process_alias(self, alias):
        return alias

    def _process_time(self, str_time):
        return self.parse_time(str_time)

    def _process_description(self, description):
        return description

    @staticmethod
    def parse_time(str_time):
        """
        >>> PlainTextParser.parse_time('1.75')
        1.75
        >>> PlainTextParser.parse_time('3')
        3.0
        >>> PlainTextParser.parse_time('0900')
        900.0
        >>> PlainTextParser.parse_time('0900-1015')
        (datetime.time(9, 0), datetime.time(10, 15))
        >>> PlainTextParser.parse_time('09:00-10:15')
        (datetime.time(9, 0), datetime.time(10, 15))
        >>> PlainTextParser.parse_time('09:00-?')
        (datetime.time(9, 0), None)
        >>> PlainTextParser.parse_time('-10:15')
        (None, datetime.time(10, 15))
        >>> PlainTextParser.parse_time('foo')
        Traceback (most recent call last):
            ...
        ParseError: The duration must be a float number or a HH:mm string
        >>> PlainTextParser.parse_time('-')
        Traceback (most recent call last):
            ...
        ParseError: The duration must be a float number or a HH:mm string
        """

        time = re.match(r'(?:(\d{1,2}):?(\d{1,2}))?-(?:(?:(\d{1,2}):?(\d{1,2}))|\?)',
                        str_time)
        time_end = None

        # HH:mm-HH:mm syntax found
        if time is not None:
            # -HH:mm syntax found
            if time.group(1) is None and time.group(2) is None:
                if time.group(3) is not None and time.group(4) is not None:
                    time_end = datetime.time(int(time.group(3)), int(time.group(4)))

                total_hours = (None, time_end)
            else:
                time_start = datetime.time(int(time.group(1)), int(time.group(2)))
                if time.group(3) is not None and time.group(4) is not None:
                    time_end = datetime.time(int(time.group(3)), int(time.group(4)))
                total_hours = (time_start, time_end)
        else:
            try:
                total_hours = float(str_time)
            except ValueError:
                raise ParseError("The duration must be a float number or a "
                                 "HH:mm string")

        return total_hours

    @staticmethod
    def extract_date(line):
        """
        >>> PlainTextParser.extract_date('1.1.2010')
        datetime.date(2010, 1, 1)
        >>> PlainTextParser.extract_date('05/08/2012')
        datetime.date(2012, 8, 5)
        >>> PlainTextParser.extract_date('05/08/12')
        datetime.date(2012, 8, 5)
        >>> PlainTextParser.extract_date('2013/08/09')
        datetime.date(2013, 8, 9)
        >>> PlainTextParser.extract_date('foobar') is None
        True
        >>> PlainTextParser.extract_date('05/08') is None
        True
        """
        # Try to match dd/mm/yyyy format
        date_matches = re.match(r'(\d{1,2})\D(\d{1,2})\D(\d{4}|\d{2})', line)

        # If no match, try with yyyy/mm/dd format
        if date_matches is None:
            date_matches = re.match(r'(\d{4})\D(\d{1,2})\D(\d{1,2})', line)

        if date_matches is None:
            return None

        # yyyy/mm/dd
        if len(date_matches.group(1)) == 4:
            return datetime.date(int(date_matches.group(1)),
                                 int(date_matches.group(2)),
                                 int(date_matches.group(3)))

        # dd/mm/yy
        if len(date_matches.group(3)) == 2:
            current_year = datetime.date.today().year
            current_millennium = current_year - (current_year % 1000)
            year = current_millennium + int(date_matches.group(3))
        # dd/mm/yyyy
        else:
            year = int(date_matches.group(3))

        return datetime.date(year, int(date_matches.group(2)),
                             int(date_matches.group(1)))

    def get_entries_direction(self):
        top_date = None

        for line in self.lines:
            date = self.extract_date(line['text'])

            if date is not None:
                if top_date is None:
                    top_date = date
                else:
                    if top_date > date:
                        return Settings.AUTO_ADD_OPTIONS['TOP']
                    elif top_date < date:
                        return Settings.AUTO_ADD_OPTIONS['BOTTOM']

        return None
