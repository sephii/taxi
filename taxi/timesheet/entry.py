from __future__ import unicode_literals

import collections

import six

from .parser import DateLine, EntryLine, TextLine, is_top_down, trim


def synchronized(func):
    """
    This decorator will run the function body only if the attribute
    ``synchronized`` of the current object is set.
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
    def __init__(self, parser, entries=None):
        super(EntriesCollection, self).__init__(EntriesList)

        self.lines = []
        self.parser = parser
        # This flag allows to enable/disable synchronization with the internal
        # text representation, useful when building the initial structure from
        # the text representation
        self.synchronized = True

        # If there are initial entries to import, disable synchronization and
        # import them in the structure
        if entries:
            self.synchronized = False

            try:
                self.init_from_str(entries)
            finally:
                self.synchronized = True

    def __repr__(self):
        return '<EntriesCollection: %s>' % super(EntriesCollection, self).__repr__()

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
        """
        If in synchronized mode, add the date and the entries to the
        textual representation.
        """
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

    def is_top_down(self):
        return is_top_down(self.lines)

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

        self.lines.insert(insert_at + 1, entry)

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
        self.lines = trim([
            line for line in self.lines
            if not isinstance(line, EntryLine) or line not in entries
        ])

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

        self.lines = trim(self.lines)

    @synchronized
    def add_date(self, date):
        """
        Add the given date to the textual representation.
        """
        self.lines = self.parser.add_date(date, self.lines)

    def init_from_str(self, entries):
        """
        Initialize the structured and textual data based on a string
        representing the entries. For detailed information about the format of
        this string, refer to the
        :func:`~taxi.timesheet.parser.parse_text` function.
        """
        self.lines = self.parser.parse_text(entries)

        for line in self.lines:
            if isinstance(line, DateLine):
                current_date = line.date
                self[current_date] = self.default_factory(self, line.date)
            elif isinstance(line, EntryLine):
                if len(self[current_date]) > 0:
                    line.previous_entry = self[current_date][-1]
                    self[current_date][-1].next_entry = line

                self[current_date].append(line)

    def to_lines(self):
        """
        Return a list of strings, each string being a line of the entries
        collection (dates, entries and text).
        """
        return [self.parser.to_text(line) for line in self.lines]


class EntriesList(list):
    """
    The EntriesList class is a classic list that synchronizes its data with the
    textual representation from the bound entries collection.
    """
    def __init__(self, entries_collection, date):
        super(EntriesList, self).__init__()

        self.entries_collection = entries_collection
        self.date = date

    def __repr__(self):
        return '<EntriesList: %s>' % super(EntriesList, self).__repr__()

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

    def append(self, x):
        """
        Append the given element to the list and synchronize the textual
        representation.
        """
        super(EntriesList, self).append(x)

        if self.entries_collection is not None:
            self.entries_collection.add_entry(self.date, x)


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
        if self.ignored:
            project_name = u'%s (ignored)' % self.alias
        else:
            project_name = self.alias

        return u'%-30s %-5.2f %s' % (project_name, self.time, self.description)

    @property
    def hours(self):
        """
        Return the sum of the duration of all entries of this aggregated entry.
        """
        return sum([entry.hours for entry in self.entries])
