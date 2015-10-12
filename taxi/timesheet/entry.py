from __future__ import unicode_literals

import collections
import datetime

import six

from .parser import DateLine, EntryLine, TextLine, TimesheetParser


def synchronized(func):
    """
    Only run the function body if the synchronized flag of the current object
    is set.
    """
    def wrapper(*args):
        if args[0].synchronized:
            return func(*args)

    return wrapper


class EntriesCollection(collections.defaultdict):
    """
    An entries collection is a subclass of defaultdict, with dates as keys and
    lists of entries (as EntriesList) as items. This collection keeps its
    structured data synchronized with a list of text lines, allowing to easily
    export it to a text format, without altering the original data.

    Use this class as you would use a standard defaultdict, it will take care
    of automatically synchronizing the textual representation with the
    structured data.
    """
    def __init__(self, entries=None, date_format='%d.%m.%Y'):
        super(EntriesCollection, self).__init__(EntriesList)

        self.lines = []
        # This flag allows to enable/disable synchronization with the internal
        # text representation, useful when building the initial structure from
        # the text representation
        self.synchronized = True
        # Whether to add new dates at the start or at the end in the textual
        # representation
        self.add_date_to_bottom = None
        self.date_format = date_format

        # If there are initial entries to import, disable synchronization and
        # import them in the structure
        if entries:
            self.synchronized = False

            try:
                self.init_from_str(entries)
            finally:
                self.synchronized = True

            try:
                self.add_date_to_bottom = self.is_top_down()
            except UnknownDirectionError:
                pass

    def __missing__(self, key):
        """
        Automatically called when the given date (key) doesn't exist. In that
        case, create the EntriesList for that key, attach it the entries
        collection (to allow callbacks when an item is added/removed) and the
        date. Also if we're in synchronized mode, add the date line to the
        textual representation.
        """
        self[key] = self.default_factory(self, key)

        return self[key]

    def __delitem__(self, key):
        """
        If in synchronized mode, delete the date and its entries from the
        textual representation.
        """
        if self.synchronized:
            self.delete_entries(self[key])
            self.delete_date(key)

        super(EntriesCollection, self).__delitem__(key)

    def __setitem__(self, key, value):
        # Delete existing lines if any
        if key in self:
            del self[key]

        # Automatically set non-supported types to an empty EntriesList. This
        # allows for things like entries[date] = []
        if not isinstance(value, self.default_factory):
            value = self.default_factory(self, key)

        super(EntriesCollection, self).__setitem__(key, value)

        if self.synchronized:
            self.add_date(key)
            for entry in value:
                self.add_entry(entry)

    @synchronized
    def add_entry(self, date, entry):
        """
        Add the given entry to the textual representation.
        """
        in_date = False
        insert_at = None

        for (lineno, line) in enumerate(self.lines):
            # Search for the date of the entry
            if isinstance(line, DateLine) and line.date == date:
                in_date = True
                # Insert here if there is no existing EntryLine for this date
                insert_at = lineno
                continue

            if in_date:
                if isinstance(line, EntryLine):
                    insert_at = lineno
                elif isinstance(line, DateLine):
                    break

        new_line = EntryLine(entry.alias, entry.duration, entry.description)
        entry.line = new_line

        self.lines.insert(insert_at + 1, new_line)

        # If there's no other EntryLine in the current date, add a blank line
        # between the date and the entry
        if not isinstance(self.lines[insert_at], EntryLine):
            self.lines.insert(insert_at + 1, TextLine(''))

    def delete_entry(self, entry):
        """
        Remove the given entry from the textual representation.
        """
        self.delete_entries([entry])

    @synchronized
    def delete_entries(self, entries):
        """
        Remove the given entries from the textual representation.
        """
        lines_to_delete = [entry.line for entry in entries]

        self.lines = [
            line for line in self.lines
            if not isinstance(line, EntryLine) or line not in lines_to_delete
        ]

        # Remove trailing whitelines
        self.trim()

    @synchronized
    def delete_date(self, date):
        """
        Remove the date line from the textual representation. This doesn't
        remove any entry line.
        """
        self.lines = [
            line for line in self.lines
            if not isinstance(line, DateLine) or line.date != date
        ]

        self.trim()

    def trim(self):
        """
        Remove blank lines at the beginning and at the end of the textual
        representation.
        """
        trim_top = None
        trim_bottom = None

        for (lineno, line) in enumerate(self.lines):
            if isinstance(line, TextLine) and not line.text.strip():
                trim_top = lineno
            else:
                break

        for (lineno, line) in enumerate(reversed(self.lines)):
            if isinstance(line, TextLine) and not line.text.strip():
                trim_bottom = lineno
            else:
                break

        if trim_top is not None:
            self.lines = self.lines[trim_top + 1:]

        if trim_bottom is not None:
            trim_bottom = len(self.lines) - trim_bottom - 1
            self.lines = self.lines[:trim_bottom]

    @synchronized
    def add_date(self, date):
        """
        Add the given date to the textual representation.
        """
        self.trim()

        if self.add_date_to_bottom:
            self.lines.append(TextLine(''))
            self.lines.append(DateLine(date, date_format=self.date_format))
        else:
            self.lines.insert(0, TextLine(''))
            self.lines.insert(0, DateLine(date, date_format=self.date_format))

        self.trim()

    def init_from_str(self, entries):
        """
        Initialize the structured and textual data based on a string
        representing the entries. For detailed information about the format of
        this string, refer to the TimesheetParser class.
        """
        self.lines = TimesheetParser.parse(entries)

        for line in self.lines:
            if isinstance(line, DateLine):
                current_date = line.date
                self[current_date] = self.default_factory(self, line.date)
            elif isinstance(line, EntryLine):
                timesheet_entry = TimesheetEntry(
                    line.alias, line.duration, line.description
                )
                timesheet_entry.ignored = line.ignored
                timesheet_entry.line = line
                if len(self[current_date]) > 0:
                    timesheet_entry.previous_entry = self[current_date][-1]
                    self[current_date][-1].next_entry = timesheet_entry

                self[current_date].append(timesheet_entry)

    def to_lines(self):
        return [line.text for line in self.lines]

    def is_top_down(self):
        date_lines = [
            line for line in self.lines if isinstance(line, DateLine)
        ]

        if len(date_lines) < 2 or date_lines[0].date == date_lines[1].date:
            raise UnknownDirectionError()
        else:
            return date_lines[1].date > date_lines[0].date


class EntriesList(list):
    """
    The EntriesList class is a classic list that synchronizes its data with the
    textual representation from the bound entries collection.
    """
    def __init__(self, entries_collection, date):
        super(EntriesList, self).__init__()

        self.entries_collection = entries_collection
        self.date = date

    def append(self, x):
        """
        Append the given element to the list and synchronize the textual
        representation.
        """
        super(EntriesList, self).append(x)

        if self.entries_collection is not None:
            self.entries_collection.add_entry(self.date, x)

    def __delitem__(self, key):
        """
        Delete the given element from the list and synchronize the textual
        representation.
        """
        if self.entries_collection is not None:
            self.entries_collection.delete_entry(self[key])

        super(EntriesList, self).__delitem__(key)

        if not self and self.entries_collection is not None:
            self.entries_collection.delete_date(self.date)


@six.python_2_unicode_compatible
class TimesheetEntry(object):
    """
    An entry is the main component of a timesheet, it has an alias, a duration
    and a description. The date is not part of the entry itself but of the
    timesheet, which contains a mapping of dates and entries.
    """
    def __init__(self, alias, duration, description):
        self.line = None
        self.ignored = False
        self.commented = False
        self.previous_entry = None
        self.next_entry = None

        self.alias = alias
        self.description = description
        self.duration = duration

    def __str__(self):
        if self.is_ignored():
            project_name = u'%s (ignored)' % self.alias
        else:
            project_name = self.alias

        return u'%-30s %-5.2f %s' % (project_name, self.hours,
                                     self.description)

    def __setattr__(self, name, value):
        """
        Apply attribute modifications to the bound line if necessary.
        """
        super(TimesheetEntry, self).__setattr__(name, value)

        if self.line is not None:
            if hasattr(self.line, name):
                setattr(self.line, name, value)

    @property
    def hash(self):
        return u'%s%s%s' % (
            self.alias,
            self.description,
            self.ignored
        )

    def is_ignored(self):
        return self.ignored or self.hours == 0

    def get_start_time(self):
        """
        Return the start time of the entry as a `datetime.time` object. If the
        start time is `None`, the end time of the previous entry will be
        returned instead. If the current entry doesn't have a duration in the
        form of a tuple, if there's no previous entry or if the previous entry
        has no end time, the value `None` will be returned.
        """
        if not isinstance(self.duration, tuple):
            return None

        if self.duration[0] is not None:
            return self.duration[0]
        else:
            if (self.previous_entry and
                    isinstance(self.previous_entry.duration, tuple) and
                    self.previous_entry.duration[1] is not None):
                return self.previous_entry.duration[1]

        return None

    @property
    def hours(self):
        """
        Return the duration of the entry in hours. If the entry has a standard
        duration, it's returned as-is. If it has a tuple duration, it will
        return the number of hours represented by the tuple.
        """
        if not isinstance(self.duration, tuple):
            return self.duration

        if self.duration[1] is None:
            return 0

        time_start = self.get_start_time()

        # This can happen if the previous entry has a non-tuple duration
        # and the current entry has a tuple duration without a start time
        if time_start is None:
            return 0

        now = datetime.datetime.now()
        time_start = now.replace(
            hour=time_start.hour,
            minute=time_start.minute, second=0
        )
        time_end = now.replace(
            hour=self.duration[1].hour,
            minute=self.duration[1].minute, second=0
        )
        total_time = time_end - time_start
        total_hours = total_time.seconds / 3600.0

        return total_hours

    def fix_start_time(self):
        """
        Set the start time of the entry to the end time of the previous entry
        if the current entry is using a tuple duration with no start time and
        the previous entry got commented.
        """
        if (isinstance(self.duration, tuple) and self.duration[0] is None
                and self.previous_entry is not None
                and self.previous_entry.commented
                and not self.commented):
            self.duration = (
                self.get_start_time(),
                self.duration[1]
            )


@six.python_2_unicode_compatible
class AggregatedTimesheetEntry(object):
    """
    Proxy class to :class:`TimesheetEntry`. An
    :class:`AggregatedTimesheetEntry` is a list of entries that have the same
    alias and description. Is is used for grouping entries.
    """
    def __init__(self):
        super(AggregatedTimesheetEntry, self).__setattr__('entries', [])

    def __getattr__(self, name):
        if not self.entries:
            raise AttributeError()

        if hasattr(self.entries[0], name):
            return getattr(self.entries[0], name)
        else:
            raise AttributeError()

    def __setattr__(self, name, value):
        for entry in self.entries:
            setattr(entry, name, value)

    def __str__(self):
        if self.is_ignored():
            project_name = u'%s (ignored)' % self.alias
        else:
            project_name = self.alias

        return u'%-30s %-5.2f %s' % (project_name, self.hours,
                                     self.description)

    @property
    def hours(self):
        return sum([entry.hours for entry in self.entries])


class UnknownDirectionError(Exception):
    pass
