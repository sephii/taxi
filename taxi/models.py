# -*- coding: utf-8 -*-
import datetime
import re

from taxi.exceptions import (
        NoActivityInProgressError,
        UndefinedAliasError,
        UnknownDirectionError
)
from taxi.parser import DateLine, EntryLine, TextLine, ParseError
from taxi.utils import date as date_utils


class Entry:
    def __init__(self, date, project_name, hours, description, id=None):
        self.project_name = project_name
        self.duration = hours
        self.description = description
        self.date = date
        self.pushed = False
        self.ignored = False
        self.local = False
        self.project_id = None
        self.activity_id = None
        self.id = id

    def __unicode__(self):
        if self.is_ignored():
            project_name = u'%s (ignored)' % (self.project_name)
        elif self.is_local():
            project_name = u'%s (local)' % (self.project_name)
        else:
            project_name = u'%s (%s/%s)' % (self.project_name, self.project_id, self.activity_id)

        return u'%-30s %-5.2f %s' % (project_name, self.get_duration() or 0, self.description)

    def is_ignored(self):
        return self.ignored or self.get_duration() == 0

    """ return true if the entry is local, ie we don't have to push it
        to Zebra
    """
    def is_local(self):
        return self.local

    def is_selected(self, exclude_ignored, exclude_local):
        return not (exclude_ignored and self.is_ignored()) and not (exclude_local and self.is_local())

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
        self.aliases = {}

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
                (self.end_date is None or self.end_date >=
                    datetime.datetime.now()))

    def get_short_status(self):
        if self.status not in self.SHORT_STATUSES:
            return '?'

        return self.SHORT_STATUSES[self.status]

    @classmethod
    def str_to_tuple(cls, string):
        """
        Converts a string in the format xxx/yyy to a (project, activity)
        tuple

        """
        matches = re.match(cls.STR_TUPLE_REGEXP, string)

        if not matches or len(matches.groups()) != 2:
            return None

        return tuple([int(item) if item else None for item in matches.groups()])

    @classmethod
    def tuple_to_str(cls, t):
        """
        Converts a (project, activity) tuple to a string in the format
        xxx/yyy

        """
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
        self.price = price

class Timesheet:
    def __init__(self, parser, mappings, date_format='%d.%m.%Y'):
        self.parser = parser
        self.mappings = mappings
        self.date_format = date_format
        self._update_entries()

    def _update_entries(self):
        self.entries = {}
        current_date = None

        for (i, line) in enumerate(self.parser.parsed_lines):
            if isinstance(line, DateLine):
                current_date = line.date

                if line.date not in self.entries:
                    self.entries[line.date] = []
            elif isinstance(line, EntryLine):
                entry = Entry(current_date, line.get_alias(), line.time,
                              line.description, i)

                if line.is_ignored():
                    entry.ignored = True

                # No start time defined, take the end time of the previous entry
                if isinstance(line.time, tuple) and line.time[0] is None:
                    if len(self.entries[current_date]) == 0:
                        raise ParseError("-HH:mm notation used but no previous "
                                         "entry to take start time from", i)
                    if (not isinstance(self.entries[current_date][-1].duration,
                                      tuple) or
                            self.entries[current_date][-1].duration[1] is None):
                        raise ParseError("-HH:mm notation used but previous "
                                         "entry doesn't have a start time", i)

                    prev_entry = self.entries[current_date][-1]
                    line.time = (prev_entry.duration[1], line.time[1])
                    entry.duration = line.time

                if entry.project_name in self.mappings:
                    entry.project_id = self.mappings[entry.project_name][0]
                    entry.activity_id = self.mappings[entry.project_name][1]

                    if(entry.project_id is None or entry.activity_id is None):
                        entry.local = True
                else:
                    if not entry.is_ignored():
                        raise UndefinedAliasError(line.get_alias())

                self.entries[current_date].append(entry)

    def get_entries(self, date=None, exclude_ignored=False, exclude_local=False):
        entries_dict = {}

        # Date can either be a single date (only 1 day) or a tuple for a
        # date range
        if date is not None and not isinstance(date, tuple):
            date = (date, date)

        for (entrydate, entries) in self.entries.iteritems():
            if date is None or (entrydate >= date[0] and entrydate <= date[1]):
                if entrydate not in entries_dict:
                    entries_dict[entrydate] = []

                d_list = [entry for entry in entries if entry.is_selected(exclude_ignored, exclude_local)]
                entries_dict[entrydate].extend(d_list)

        return entries_dict

    def get_local_entries(self, date=None):
        entries_dict = self.get_entries(date, False)
        local_entries = {}

        for (date, entries) in entries_dict.iteritems():
            local_entries_list = [entry for entry in entries if entry.is_local()]

            if local_entries_list:
                local_entries[date] = local_entries_list

        return local_entries

    def get_ignored_entries(self, date=None):
        entries_dict = self.get_entries(date, False)
        ignored_entries = {}

        for (date, entries) in entries_dict.iteritems():
            ignored_entries_list = []
            for entry in entries:
                if entry.is_ignored():
                    ignored_entries_list.append(entry)

            if ignored_entries_list:
                ignored_entries[date] = ignored_entries_list

        return ignored_entries

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

    def _get_date_line(self, date):
        for (i, line) in enumerate(self.parser.parsed_lines):
            if isinstance(line, DateLine) and line.date == date:
                return i

        return None

    def add_entry(self, entry, add_to_bottom=True):
        new_entry = EntryLine(entry.project_name, entry.duration,
                              entry.description)

        if new_entry.get_alias() not in self.mappings:
            raise UndefinedAliasError(new_entry.get_alias())

        last_entry_line = self._get_latest_entry_for_date(entry.date)

        # An entry already exists for this date, we'll just add the new one
        # after that one
        if last_entry_line is not None:
            self.parser.parsed_lines.insert(last_entry_line + 1, new_entry)
        else:
            date_line_number = self._get_date_line(entry.date)
            blank_line = TextLine('')

            # The date is already in the timesheet but it doesn't have any entry
            if date_line_number is not None:
                index = date_line_number + 1

                try:
                    if (isinstance(self.parser.parsed_lines[index], TextLine)
                            and self.parser.parsed_lines[index].text == ''):
                        self.parser.parsed_lines.insert(index + 1, blank_line)
                        self.parser.parsed_lines.insert(index + 1, new_entry)
                    else:
                        self.parser.parsed_lines.insert(index, blank_line)
                        self.parser.parsed_lines.insert(index, new_entry)
                        self.parser.parsed_lines.insert(index, blank_line)
                except IndexError:
                    self.parser.parsed_lines.insert(index, new_entry)
                    self.parser.parsed_lines.insert(index, blank_line)
            else:
                is_empty = self.is_empty()

                if add_to_bottom:
                    index = len(self.parser.parsed_lines)
                else:
                    index = 0
                    self.parser.parsed_lines.insert(index, blank_line)

                date_line = DateLine(entry.date, date_format=self.date_format)
                self.parser.parsed_lines.insert(index, new_entry)
                self.parser.parsed_lines.insert(index, blank_line)
                self.parser.parsed_lines.insert(index, date_line)

                # Add a trailing blank line to separate the new date from the
                # next date
                if add_to_bottom and not is_empty:
                    self.parser.parsed_lines.insert(index, blank_line)

        self._update_entries()

    def is_empty(self):
        """
        Return True if the timesheet doesn't contain any line.
        """
        return len(self.parser.parsed_lines) == 0

    def continue_entry(self, date, end, description=None):
        last_entry_line = self._get_latest_entry_for_date(date)

        if (last_entry_line is None or not
                isinstance(self.parser.parsed_lines[last_entry_line].time, tuple) or
                self.parser.parsed_lines[last_entry_line].time[1] is not None):
            raise NoActivityInProgressError()

        last_entry = self.parser.parsed_lines[last_entry_line]

        start_date = datetime.datetime.combine(date, last_entry.time[0])
        end_date = datetime.datetime.combine(date, end)
        difference_minutes = (end_date - start_date).seconds / 60
        remainder = difference_minutes % 15
        # round up
        difference_minutes += 15 - remainder if remainder > 0 else 0
        rounded_time = (start_date +
                        datetime.timedelta(minutes=difference_minutes))

        new_entry = EntryLine(last_entry.alias, (last_entry.time[0],
                              rounded_time), description or '?')

        self.parser.parsed_lines[last_entry_line] = new_entry

    def prefill(self, auto_fill_days, limit=None, add_to_bottom=True):
        entries = self.get_entries()

        if len(entries) == 0:
            today = datetime.date.today()
            cur_date = datetime.date(today.year, today.month, 1)
        else:
            cur_date = max([date for (date, entries) in entries.iteritems()])
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

        for (date, date_entries) in entries.iteritems():
            if date not in (today, yesterday) or date.strftime('%w') in [6, 0]:
                if date_entries:
                    non_workday_entries.append((date, date_entries))

        return non_workday_entries

    def comment_entries(self, entries):
        for entry in entries:
            if entry.id is None:
                raise Exception(u"Couldn't comment entry `%s` because it "
                                "doesn't have an id" % unicode(entry))

            l = self.parser.parsed_lines[entry.id]

            if not isinstance(l, EntryLine):
                raise Exception(u"Couldn't comment entry `%s` because it "
                                "is not an EntryLine" % unicode(l))

            new_text_line = TextLine(unicode(l))
            new_text_line.comment()
            self.parser.parsed_lines[entry.id] = new_text_line

        self._update_entries()

    def is_top_down(self):
        """
        Returns True if the most recent entries are on the bottom of the file,
        False otherwise. Raises UnknownDirectionError if it's unable to detect
        it.

        """
        date = None
        for line in self.parser.parsed_lines:
            if isinstance(line, DateLine):
                if date is None:
                    date = line.date
                else:
                    if date != line.date:
                        return date < line.date

        raise UnknownDirectionError()

    def fix_entries_start_time(self):
        """
        Fixes the start time of entries in -HH:mm notation that are not pushed
        but follow an entry that has been pushed. See
        https://github.com/sephii/taxi/issues/18 for more details.
        """
        for date, entries in self.entries.iteritems():
            previous_entry = None

            for entry in entries:
                # Look for an entry that has not been pushed, and that uses
                # the -HH:mm notation
                if (previous_entry is not None
                        and not entry.pushed
                        and isinstance(entry.duration, tuple)):
                    entry_line = self.parser.parsed_lines[entry.id]
                    entry_line.text = entry_line.generate_text()
                elif entry.pushed:
                    previous_entry = entry
