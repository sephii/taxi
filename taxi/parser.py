# -*- coding: utf-8 -*-
import codecs
import re
import string
import datetime
import os

from taxi.exceptions import ProjectNotFoundError
from taxi.settings import Settings
from taxi.utils import date as date_utils

class ParseError(Exception):
    pass

class TextLine(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text

class EntryLine(TextLine):
    def __init__(self, alias, time, description, text=None):
        self.alias = alias
        self.time = time
        self.description = description

        if text is not None:
            self.text = text
        else:
            if isinstance(self.time, tuple):
                time = '%s-%s' % (self.time[0].strftime('%H:%M'),
                                  self.time[1].strftime('%H:%M') if self.time[1]
                                  is not None else '?')
            else:
                time = self.time

            self.text = '%s %s %s' % (self.alias, time, self.description)

    def is_ignored(self):
        return self.alias.endswith('?')

    def get_alias(self):
        if self.alias.endswith('?'):
            return self.alias[0:-1]

        return self.alias

class DateLine(TextLine):
    def __init__(self, date, text=None, date_format='%d.%m.%Y'):
        self.date = date

        if text is not None:
            self.text = text
        else:
            self.text = self.date.strftime(date_format)

class Parser(object):
    def parse(self):
        self.current_line_number = 1

        try:
            for line in self.lines:
                self.parsed_lines.append(self.parse_line())
                self.current_line_number += 1
        except Exception as e:
            raise
            raise ParseError("Line #%s is not correctly formatted (error was "
                             " '%s')" % (self.current_line_number, e.message))

    def parse_line(self):
        raise NotImplementedError()

    def _get_current_line(self):
        return self.lines[self.current_line_number - 1]

    def __init__(self, lines):
        self.entries = {}
        self.lines = lines
        self.parsed_lines = []

        self.parse()

class TaxiParser(Parser):
    r"""
    >>> t = TaxiParser([
    ... '01.01.2013', '\n', 'foobar 0900-1000 baz', '# comment',
    ... 'foo -1100 bar'])
    ...
    >>> len(t.parsed_lines)
    5
    >>> type(t.parsed_lines[0])
    <class 'parser.DateLine'>
    >>> t.parsed_lines[0].date
    datetime.date(2013, 1, 1)
    >>> type(t.parsed_lines[1])
    <class 'parser.TextLine'>
    >>> t.parsed_lines[1].text
    ''
    >>> type(t.parsed_lines[2])
    <class 'parser.EntryLine'>
    >>> t.parsed_lines[2].alias
    'foobar'
    >>> t.parsed_lines[2].time
    (datetime.time(9, 0), datetime.time(10, 0))
    >>> t.parsed_lines[2].description
    'baz'
    >>> type(t.parsed_lines[3])
    <class 'parser.TextLine'>
    >>> t.parsed_lines[3].text
    '# comment'
    >>> t.parsed_lines[4].alias
    'foo'
    >>> t.parsed_lines[4].time
    (None, datetime.time(11, 0))
    >>> t.parsed_lines[4].description
    'bar'
    """

    def __init__(self, file):
        self.current_date = None
        super(TaxiParser, self).__init__(file)

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
                raise ParseError('Entries must be defined inside a date section')

            return self._parse_entry_line(line)

    def _parse_entry_line(self, line):
        split_line = string.split(s=line, maxsplit=2)

        if len(split_line) != 3:
            raise ParseError()

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
        >>> TaxiParser.parse_time('1.75')
        1.75
        >>> TaxiParser.parse_time('3')
        3.0
        >>> TaxiParser.parse_time('0900')
        900.0
        >>> TaxiParser.parse_time('0900-1015')
        (datetime.time(9, 0), datetime.time(10, 15))
        >>> TaxiParser.parse_time('09:00-10:15')
        (datetime.time(9, 0), datetime.time(10, 15))
        >>> TaxiParser.parse_time('09:00-?')
        (datetime.time(9, 0), None)
        >>> TaxiParser.parse_time('-10:15')
        (None, datetime.time(10, 15))
        >>> TaxiParser.parse_time('foo')
        Traceback (most recent call last):
            ...
        ParseError: The duration must be a float number or a HH:mm string
        >>> TaxiParser.parse_time('-')
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
        >>> TaxiParser.extract_date('1.1.2010')
        datetime.date(2010, 1, 1)
        >>> TaxiParser.extract_date('05/08/2012')
        datetime.date(2012, 8, 5)
        >>> TaxiParser.extract_date('05/08/12')
        datetime.date(2012, 8, 5)
        >>> TaxiParser.extract_date('2013/08/09')
        datetime.date(2013, 8, 9)
        >>> TaxiParser.extract_date('foobar') is None
        True
        >>> TaxiParser.extract_date('05/08') is None
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

    def update_file(self):
        file = codecs.open(self.file, 'w', 'utf-8')

        for line in self.lines:
            file.write(line)

        file.close()

    def get_line_text(self, entry):
        if isinstance(entry.duration, tuple):
            if entry.duration[0] is not None:
                txtduration = entry.duration[0].strftime('%H:%M')

                if entry.duration[1] is not None:
                    txtduration += '-%s' % entry.duration[1].strftime('%H:%M')
                else:
                    txtduration += '-?'
            else:
                txtduration = '?'
        else:
            txtduration = entry.duration

        return (u'%s %s %s\n' % (entry.project_name, txtduration,
                entry.description or '?'))

    def auto_add(self, mode, new_date = datetime.date.today(),
                 date_format='%d/%m/%Y'):
        # Check if we already have the current date in the file
        for line in self.lines:
            date = self.extract_date(line['text'])

            if date is not None and date == new_date:
                return

        if mode == Settings.AUTO_ADD_OPTIONS['TOP']:
            self.lines.insert(0, {
                'text': '%s\n' %
                    new_date.strftime(date_format),
                'entry': None
            })
            self.lines.insert(1, {'text': '\n', 'entry': None})
        elif mode == Settings.AUTO_ADD_OPTIONS['BOTTOM']:
            if len(self.lines) > 0:
                self.lines.append({'text': '\n', 'entry': None})

            self.lines.append({
                'text': '%s\n' %
                    new_date.strftime(date_format),
                'entry': None
            })
            self.lines.append({'text': '\n', 'entry': None})

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

    def check_mappings(self, aliases):
        for (date, entries) in self.entries.iteritems():
            for entry in entries:
                if not entry.is_ignored() and entry.project_name not in aliases:
                    raise ProjectNotFoundError(entry.project_name)

    def get_non_current_workday_entries(self, limit_date=None):
        non_workday_entries = []
        entries = self.get_entries(limit_date, exclude_ignored=True)
        today = datetime.date.today()
        yesterday = date_utils.get_previous_working_day(today)

        for (date, date_entries) in entries:
            if date not in (today, yesterday) or date.strftime('%w') in [6, 0]:
                if date_entries:
                    non_workday_entries.append((date, date_entries))

        return non_workday_entries
