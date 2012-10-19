# -*- coding: utf-8 -*-
import codecs
import re
import string
import datetime
import os

from taxi.exceptions import ProjectNotFoundError
# TODO
#from taxi.settings import settings
from taxi.settings import Settings
from taxi.utils import date as date_utils

class ParseError(Exception):
    pass

class ParsedFile(object):
    def __init__(self):
        self.entries = {}

    def add_entry(self, date, entry):
        if date not in self.entries:
            self.entries[date] = []

        self.entries[date].append(entry)

    @staticmethod
    def is_entry_ignored(entry):
        return entry[0].endswith('?')

    def get_entry_duration(entry):
        pass

    def get_entries(self, date=None):
        if not date:
            return self.entries

        if date in self.entries:
            return self.entries[date]

        return []

class Parser(object):
    def process_line(self, line, line_number):
        pass

    def parse(self):
        file = codecs.open(self.file, 'r', 'utf-8')
        self.lines = file.readlines()
        self.current_line_number = 1

        try:
            for line in self.lines:
                self.parse_line()
                self.current_line_number += 1
        except Exception as e:
            raise
            raise ParseError('Line #%s is not correctly formatted (error was'\
                    ' \'%s\')' % (self.current_line_number, e.message))

        file.close()

    def _get_current_line(self):
        return self.lines[self.current_line_number - 1]

    def __init__(self, file):
        if not os.path.exists(file):
            raise ParseError('File %s does not exist' % file)

        self.parsed_file = ParsedFile()
        self.file = file
        self.entries = {}
        self.lines = []

        self.parse()

class TaxiParser(Parser):
    def __init__(self, file):
        self.current_date = None
        self.parsed_lines = {}
        super(TaxiParser, self).__init__(file)

    def _process_date(self, date_matches):
        if len(date_matches.group(1)) == 4:
            return datetime.date(int(date_matches.group(1)), int(date_matches.group(2)), int(date_matches.group(3)))

        if len(date_matches.group(3)) == 2:
            current_year = datetime.date.today().year
            current_millennium = current_year - (current_year % 1000)
            year = current_millennium + int(date_matches.group(3))
        else:
            year = int(date_matches.group(3))

        return datetime.date(year, int(date_matches.group(2)), int(date_matches.group(1)))

    def _match_date(self, line):
        # Try to match dd/mm/yyyy format
        match = re.match(r'(\d{1,2})\D(\d{1,2})\D(\d{4}|\d{2})', line)

        # If no match, try with yyyy/mm/dd format
        if match is None:
            match = re.match(r'(\d{4})\D(\d{1,2})\D(\d{1,2})', line)

        return match

    def parse_line(self):
        line = self._get_current_line().strip()

        if len(line) == 0 or line[0] == '#':
            return

        date_matches = self._match_date(line)

        if date_matches is not None:
            self.current_date = self._process_date(date_matches)
            print(self.current_date)
        else:
            if self.current_date is None:
                raise ParseError('Entries must be defined inside a date section')

            entry = self._parse_entry_line(line)
            self.parsed_lines[self.current_line_number] = entry
            self.parsed_file.add_entry(self.current_date, entry)

    def _parse_entry_line(self, line):
        split_line = string.split(s=line, maxsplit=2)

        if len(split_line) == 0:
            return
        elif len(split_line) != 3:
            raise ParseError()

        alias = self._process_alias(split_line[0])
        time = self._process_time(split_line[1])
        description = self._process_description(split_line[2])

        return (alias, time, description)

    def _process_alias(self, alias):
        return alias

    def _process_time(self, str_time):
        time = re.match(r'(?:(\d{1,2}):?(\d{1,2}))?-(?:(?:(\d{1,2}):?(\d{1,2}))|\?)',
                        str_time)
        time_end = None

        # HH:mm-HH:mm syntax found
        if time is not None:
            # -HH:mm syntax found
            if time.group(1) is None and time.group(2) is None:
                my_line_number = self.current_line_number
                prev_time = None

                # Browse previous lines to find an entry with an end date
                while my_line_number > 0:
                    my_line_number -= 1

                    # Date line detected, but no previous candidate found
                    if self._match_date(self.lines[my_line_number]):
                        break

                    if my_line_number in self.parsed_lines:
                        prev_time = self.parsed_lines[my_line_number][1]
                        break

                if prev_time is None:
                    print(self.parsed_lines)
                    raise ParseError('No previous entry to take time from')
                else:
                    if (not isinstance(prev_time, tuple) or
                            prev_time[1] is None):
                        raise ParseError('The previous entry must use HH:mm notation and have an end time')

                    if time.group(3) is not None and time.group(4) is not None:
                        time_end = datetime.time(int(time.group(3)), int(time.group(4)))

                    total_hours = (prev_time[1], time_end)
            else:
                time_start = datetime.time(int(time.group(1)), int(time.group(2)))
                if time.group(3) is not None and time.group(4) is not None:
                    time_end = datetime.time(int(time.group(3)), int(time.group(4)))
                total_hours = (time_start, time_end)
        else:
            try:
                total_hours = float(str_time)
            except ValueError:
                raise ParseError('The duration must be a number (eg. 0.75, 2, etc)' \
                                 ' or a HH:mm string')

        return total_hours

    def _process_description(self, description):
        return description

    def update_file(self):
        file = codecs.open(self.file, 'w', 'utf-8')

        for line in self.lines:
            text = line['text']

            if line['entry'] is not None and line['entry'].pushed:
                text = '# %s' % text

            file.write(text)

        file.close()

    def get_entries(self, date=None, exclude_ignored=False):
        entries_list = []

        # Date can either be a single date (only 1 day) or a tuple for a
        # date range
        if date is not None and not isinstance(date, tuple):
            date = (date, date)

        for (entrydate, entries) in self.entries.iteritems():
            if date is None or (entrydate >= date[0] and entrydate <= date[1]):
                if not exclude_ignored:
                    entries_list.append((entrydate, entries))
                else:
                    d_list = [entry for entry in entries if not entry.is_ignored()]
                    entries_list.append((entrydate, d_list))

        return entries_list

    def add_entry(self, date, project, duration=None, direction=None):
        if date not in self.entries:
            self.entries[date] = []

        # TODO
        new_entry = Entry(date, project, duration, '?')
        new_text = self.get_line_text(new_entry)

        new_line = {
                'entry': new_entry,
                'text': new_text,
        }
        self.entries[date].append(new_entry)

        current_date = None
        latest_entry = None
        latest_entry_is_date = False

        for lineno, line in enumerate(self.lines):
            if line['entry'] is None:
                datematches = self._match_date(line['text'])
                if datematches is not None:
                    current_date = self.process_date(datematches)

                    # We're on the current date, store the line number
                    if current_date == date:
                        latest_entry = lineno
                        latest_entry_is_date = True
                    # We passed the current date and we already found the
                    # current date, break
                    elif latest_entry is not None:
                        break
                # The line contains something else that an entry and a date and
                # it's not just a blank line
                elif len(line['text'].strip()) > 0 and latest_entry is not None:
                    latest_entry = lineno
                    latest_entry_is_date = False
            # We're on the current date (latest_entry is set) and we're on an
            # entry, store the line number
            elif latest_entry is not None:
                latest_entry = lineno
                latest_entry_is_date = False

        # There's already an entry for this date: append the new one
        if latest_entry is not None:
            if latest_entry_is_date:
                new_line['text'] = '\n' + new_line['text']
            self.lines.insert(latest_entry + 1, new_line)
        # No date in the file, we need to add it
        else:
            to_insert = [
                {
                    'text': '%s\n' % 
                        date.strftime(settings.get('default', 'date_format')),
                    'entry': None
                },
                {'text': '\n', 'entry': None},
                new_line,
            ]

            if direction is None or direction == settings.AUTO_ADD_OPTIONS['TOP']:
                for i in range(len(to_insert)):
                    self.lines.insert(i, to_insert[i])
                self.lines.insert(len(to_insert), {'text': '\n', 'entry': None})
            elif direction == settings.AUTO_ADD_OPTIONS['BOTTOM']:
                self.lines.append({'text': '\n', 'entry': None})
                for line in to_insert:
                    self.lines.append(line)

    def continue_entry(self, date, end, description=None):
        found_entry = None
        for entry in self.entries[date]:
            if isinstance(entry.duration, tuple) and entry.duration[1] is None:
                found_entry = entry
                break

        if found_entry is None:
            raise Exception('Error: no activity in progress found')

        for lineno, line in enumerate(self.lines):
            if line['entry'] == found_entry:
                t = (datetime.datetime.now() - (datetime.datetime.combine(datetime.datetime.today(), found_entry.duration[0]))).seconds / 60
                print(u'Elapsed time is %i minutes' % t)
                r = t % 15
                t += 15 - r if r != 0 else 0
                print(u'It will be rounded to %i minutes' % t)
                rounded_time = (datetime.datetime.combine(datetime.datetime.today(), found_entry.duration[0]) + datetime.timedelta(minutes = t))
                found_entry.duration = (found_entry.duration[0], rounded_time)
                found_entry.description = description or '?'
                self.lines[lineno]['text'] = self.get_line_text(found_entry)

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
            date_matches = self._match_date(line['text'])

            if date_matches is not None:
                date = self.process_date(date_matches)

                if date == new_date:
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
            date_matches = self._match_date(line['text'])

            if date_matches is not None:
                date = self.process_date(date_matches)

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
