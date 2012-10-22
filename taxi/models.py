# -*- coding: utf-8 -*-
import codecs
import datetime
import re

from taxi.parser import DateLine, EntryLine, TextLine
from taxi.exceptions import UndefinedAliasError

class Entry:
    def __init__(self, date, project_name, hours, description):
        self.project_name = project_name
        self.duration = hours
        self.description = description
        self.date = date
        self.pushed = False
        self.ignored = False
        self.project_id = None
        self.activity_id = None

    def __unicode__(self):
        if self.is_ignored():
            project_name = u'%s (ignored)' % (self.project_name)
        else:
            project_name = u'%s (%s/%s)' % (self.project_name, self.project_id, self.activity_id)

        return u'%-30s %-5.2f %s' % (project_name, self.get_duration() or 0, self.description)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def is_ignored(self):
        return self.ignored or self.get_duration() == 0

    def get_duration(self):
        if isinstance(self.duration, tuple):
            if None in self.duration:
                return 0

            now = datetime.datetime.now()
            time_start = now.replace(hour=self.duration[0].hour,\
                    minute=self.duration[0].minute, second=0)
            time_end = now.replace(hour=self.duration[1].hour,\
                    minute=self.duration[1].minute, second=0)
            total_time = time_end - time_start
            total_hours = total_time.seconds / 3600.0

            return total_hours

        return self.duration

class Project:
    STATUS_NOT_STARTED = 0
    STATUS_ACTIVE = 1
    STATUS_FINISHED = 2
    STATUS_CANCELLED = 3

    STATUSES = {
            STATUS_NOT_STARTED: 'Not started',
            STATUS_ACTIVE: 'Active',
            STATUS_FINISHED: 'Finished',
            STATUS_CANCELLED: 'Cancelled',
    }

    SHORT_STATUSES = {
            STATUS_NOT_STARTED: 'N',
            STATUS_ACTIVE: 'A',
            STATUS_FINISHED: 'F',
            STATUS_CANCELLED: 'C',
    }

    STR_TUPLE_REGEXP = r'^(\d{1,4})(?:/(\d{1,4}))?$'

    def __init__(self, id, name, status = None, description = None, budget = None):
        self.id = int(id)
        self.name = name
        self.activities = []
        self.status = int(status)
        self.description = description
        self.budget = budget

    def __unicode__(self):
        if self.status in self.STATUSES:
            status = self.STATUSES[self.status]
        else:
            status = 'Unknown'

        start_date = self.get_formatted_date(self.start_date)
        if start_date is None:
            start_date = 'Unknown'

        end_date = self.get_formatted_date(self.end_date)
        if end_date is None:
            end_date = 'Unknown'

        return u"""Id: %s
Name: %s
Status: %s
Start date: %s
End date: %s
Budget: %s
Description: %s""" % (
        self.id, self.name,
        status,
        start_date,
        end_date,
        self.budget,
        self.description
    )

    def __str__(self):
        return unicode(self).encode('utf-8')

    def get_formatted_date(self, date):
        if date is not None:
            try:
                formatted_date = date.strftime('%d.%m.%Y')
            except ValueError:
                formatted_date = None
        else:
            formatted_date = None

        return formatted_date

    def add_activity(self, activity):
        self.activities.append(activity)

    def get_activity(self, id):
        for activity in self.activities:
            if activity.id == id:
                return activity

        return None

    def is_active(self):
        return (self.status == self.STATUS_ACTIVE and
                (self.start_date is None or
                    self.start_date <= datetime.datetime.now()) and
                (self.end_date is None or self.end_date >
                    datetime.datetime.now()))

    def get_short_status(self):
        if self.status not in self.SHORT_STATUSES:
            return '?'

        return self.SHORT_STATUSES[self.status]

    @classmethod
    def str_to_tuple(cls, string):
        """Converts a string in the format xxx/yyy to a (project, activity)
        tuple"""
        matches = re.match(cls.STR_TUPLE_REGEXP, string)

        if not matches or len(matches.groups()) != 2:
            return None

        return tuple([int(item) if item else None for item in matches.groups()])

    @classmethod
    def tuple_to_str(cls, t):
        """Converts a (project, activity) tuple to a string in the format
        xxx/yyy"""
        if len(t) != 2:
            return None

        if t[1] is not None:
            return u'%s/%s' % t
        else:
            return unicode(t[0])

class Activity:
    def __init__(self, id, name, price):
        self.id = int(id)
        self.name = name
        self.price = float(price)

class Timesheet:
    r"""
    >>> from taxi.parser.io import StreamIo
    >>> from taxi.parser.parsers.plaintext import PlainTextParser
    >>> m = {'foo': (123, 456), 'bar': (12, 34)}
    >>> si = StreamIo("10.10.2012\nfoo 09:00-10:00 baz")
    >>> p = PlainTextParser(si)
    >>> t = Timesheet(p, m, '%d.%m.%Y')
    >>> t.get_entries() # doctest: +ELLIPSIS
    [(datetime.date(2012, 10, 10), [<models.Entry instance at 0x...>])]
    >>> t.to_lines()
    ['10.10.2012', 'foo 09:00-10:00 baz']
    >>> e = Entry(datetime.date(2012, 10, 10), 'bar', 2, 'baz')
    >>> t.add_entry(e)
    >>> t.get_entries() # doctest: +ELLIPSIS
    [(datetime.date(2012, 10, 10), [<models.Entry instance at 0x...>, <models.Entry instance at 0x...])]
    >>> t.to_lines()
    ['10.10.2012', 'foo 09:00-10:00 baz', 'bar 2 baz']
    >>> e = Entry(datetime.date(2012, 10, 21), 'baz', (datetime.time(9, 0),
    ... None), 'baz')
    >>> t.add_entry(e)
    Traceback (most recent call last):
    ...
    UndefinedAliasError: baz
    >>> t.to_lines()
    ['10.10.2012', 'foo 09:00-10:00 baz', 'bar 2 baz']
    """
    def __init__(self, parser, mappings, date_format='%d.%m.%Y'):
        self.parser = parser
        self.mappings = mappings
        self.date_format = date_format
        self._update_entries()

    def _update_entries(self):
        self.entries = {}
        current_date = None

        for line in self.parser.parsed_lines:
            if isinstance(line, DateLine):
                current_date = line.date

                if line.date not in self.entries:
                    self.entries[line.date] = []
            elif isinstance(line, EntryLine):
                entry = Entry(current_date, line.alias, line.time, line.description)

                if line.is_ignored():
                    entry.ignored = True

                if line.get_alias() in self.mappings:
                    entry.project_id = self.mappings[entry.project_name][0]
                    entry.activity_id = self.mappings[entry.project_name][1]
                else:
                    raise UndefinedAliasError(line.get_alias())

                if isinstance(line.time, tuple) and line.time[0] is None:
                    if len(self.entries[current_date]) == 0:
                        raise Exception("no previous date")
                    if not isinstance(self.entries[current_date][-1].duration,
                                      tuple):
                        raise Exception("not a tuple")

                    prev_entry = self.entries[current_date][-1]
                    line.time = (prev_entry.duration[1], line.time[1])
                    entry.duration = line.time

                self.entries[current_date].append(entry)

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

    def _get_latest_entry_for_date(self, date):
        date_line = None
        last_entry_line = None

        for (i, line) in enumerate(self.parser.parsed_lines):
            if isinstance(line, DateLine) and line.date == date:
                date_line = i
            elif date_line is not None:
                if isinstance(line, EntryLine):
                    last_entry_line = i
                elif isinstance(line, DateLine):
                    # Reset date_line in the case the date is twice in the
                    # timesheet, once without any entry
                    date_line = None

        return last_entry_line

    def add_entry(self, entry, add_to_bottom=True):
        new_entry = EntryLine(entry.project_name, entry.duration,
                              entry.description)

        if new_entry.get_alias() not in self.mappings:
            raise UndefinedAliasError(new_entry.get_alias())

        last_entry_line = self._get_latest_entry_for_date(entry.date)

        if last_entry_line is not None:
            self.parser.parsed_lines.insert(last_entry_line + 1, new_entry)
        else:
            if add_to_bottom:
                index = len(self.parser.parsed_lines)
            else:
                index = 0

            date_line = DateLine(entry.date, date_format=self.date_format)
            blank_line = TextLine('')

            if not add_to_bottom:
                self.parser.parsed_lines.insert(index, blank_line)

            self.parser.parsed_lines.insert(index, new_entry)
            self.parser.parsed_lines.insert(index, blank_line)
            self.parser.parsed_lines.insert(index, date_line)

        self._update_entries()

    def continue_entry(self, date, end, description=None):
        last_entry_line = self._get_latest_entry_for_date(date)

        if (last_entry_line is None or not
                isinstance(self.parser.parsed_lines[last_entry_line].date, tuple) or
                self.parser.parsed_lines[last_entry_line].duration[1] is not None):
            raise ParseError("No activity in progress found")

        last_entry = self.parser.parsed_lines[last_entry_line]

        t = (datetime.datetime.now() -
            (datetime.datetime.combine(datetime.datetime.today(),
                last_entry.duration[0]))).seconds / 60
        r = t % 15
        t += 15 - r if r != 0 else 0
        rounded_time = (datetime.datetime.combine(datetime.datetime.today(),
            last_entry.duration[0]) + datetime.timedelta(minutes = t))
        last_entry.duration = (found_entry.duration[0], rounded_time)
        last_entry.description = description or '?'

        self.parser.parsed_lines[last_entry_line] = last_entry

    def prefill(self, auto_fill_days, limit=None, add_to_bottom=True):
        entries = self.get_entries()

        if len(entries) == 0:
            today = datetime.date.today()
            cur_date = datetime.date(today.year, today.month, 1)
        else:
            cur_date = max([date for (date, entries) in entries])
            cur_date += datetime.timedelta(days = 1)

        if limit is None:
            limit = datetime.date.today()

        while cur_date <= limit:
            if cur_date.weekday() in auto_fill_days:
                self.add_date(cur_date, add_to_bottom)

            cur_date = cur_date + datetime.timedelta(days = 1)

    def add_date(self, date, add_to_bottom=True):
        # Check if we already have the current date in the file
        if date in self.entries:
            return

        if add_to_bottom:
            index = len(self.parser.parsed_lines)
        else:
            index = 0

        self.parser.parsed_lines.insert(index, TextLine(''))
        self.parser.parsed_lines.insert(index, DateLine(date, date_format=self.date_format))
        self._update_entries()

    def save(self):
        self.parser.save()

    def to_lines(self):
        lines = []

        for line in self.parser.parsed_lines:
            lines.append(line.text)

        return lines

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
