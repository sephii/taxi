import collections
import copy
import datetime

from ..aliases import aliases_database
from ..exceptions import EntriesCollectionValidationError
from ..utils import date as date_utils
from .flags import FlaggableMixin
from .lines import DateLine, TextLine
from .utils import is_top_down, trim


def synchronized(func):
    """
    This decorator will run the function body only if the attribute
    ``synchronized`` of the current object is set.
    """
    def wrapper(*args):
        if args[0].synchronized:
            return func(*args)

    return wrapper


class Entry(FlaggableMixin):
    """
    The Entry is a line representing a timesheet entry, with an alias, a
    duration, a description and some potential flags.
    """
    FLAG_IGNORED = 'ignored'
    FLAG_PUSHED = 'pushed'

    def __init__(self, alias, duration, description, flags=None, text=None):
        """
        `flags` must be a :class:`set` of flags (either :attr:`FLAG_IGNORED` or :attr:`FLAG_PUSHED`).

        If `text` is set, it will be used as a base by the parser, with any necessary modification depending on the
        attributes that have been set on the :class:`Entry`. `text` must be a tuple in the following form::

            (flags, space1, alias, space2, duration, space3, description)

        Where `space1`, `space2` and `space3` are just spacing characters (this is used to preserve the number of
        whitespaces when regenerating the line). For the values of `flags`, `alias`, `duration` and `description`,
        refer to the :class:`~taxi.timesheet.parser.TimesheetParser` class.

        """
        super(Entry, self).__init__()

        self._text = text
        self.alias = alias
        self.duration = duration
        self.description = description
        self.previous_entry = None

        # Flags *must* be changed through the dedicated methods, or we won't notice it and we won't be able to reflect
        # the change when outputting the line as text
        if flags is not None:
            self._flags = copy.copy(flags)

        # This must come last in the initialization as any attribute set after this one will be recorded in
        # `_changed_attrs`
        self._changed_attrs = set()

    def __repr__(self):
        return '<Entry: "%s">' % self.__str__()

    def __str__(self):
        return "{alias} {time} {description}".format(alias=self.alias, time=self.hours, description=self.description)

    def __setattr__(self, attr, value):
        """
        Set the given `attr` to the given `value` and memorize this attribute
        has changed so we can regenerate it when outputting text.
        """
        if hasattr(self, '_changed_attrs') and attr != '_changed_attrs':
            self._changed_attrs.add(attr)

        super(Entry, self).__setattr__(attr, value)

    @property
    def hours(self):
        """
        Return the number of hours this entry has lasted. If the duration is a tuple with a start and an end time,
        the difference between the two times will be calculated. If the duration is a number, it will be returned
        as-is.
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

    @property
    def in_progress(self):
        return isinstance(self.duration, tuple) and self.duration[1] is None

    @property
    def mapped(self):
        return self.alias in aliases_database

    def get_start_time(self):
        """
        Return the start time of the entry as a :class:`datetime.time` object.
        If the start time is `None`, the end time of the previous entry will be
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
    def hash(self):
        """
        Return a value that's used to uniquely identify an entry in a date so we can regroup all entries that share the
        same hash.
        """
        return u''.join([
            self.alias,
            self.description,
            str(self.ignored),
            str(self.flags),
        ])

    def add_flag(self, flag):
        """
        Add flag to the flags and memorize this attribute has changed so we can
        regenerate it when outputting text.
        """
        super(Entry, self).add_flag(flag)
        self._changed_attrs.add('flags')

    def remove_flag(self, flag):
        """
        Remove flag to the flags and memorize this attribute has changed so we
        can regenerate it when outputting text.
        """
        super(Entry, self).remove_flag(flag)
        self._changed_attrs.add('flags')

    @property
    def flags(self):
        """
        Return a copy of the flags. The reason why we return a copy and not the
        original flags is that we don't want it to be altered because we need
        to keep the synchronisation with the text lines. To change a flag, use
        :meth:`add_flag` or :meth:`remove_flag` or use shortcut properties such
        as :attr:`ignored` or :attr:`pushed`.
        """
        return copy.copy(self._flags)

    @property
    def pushed(self):
        """
        Return True if the object has the :attr:`FLAG_PUSHED` flag set.
        """
        return self.has_flag(self.FLAG_PUSHED)

    @pushed.setter
    def pushed(self, value):
        """
        Set the ignored flag if the `value` it is set to evaluates to True,
        remove it otherwise.
        """
        self._add_or_remove_flag(self.FLAG_PUSHED, value)

    @property
    def ignored(self):
        """
        Return True if this entry is supposed to be ignored, False otherwise. A
        line can be ignored for several reasons:

            * It has the ignored flag set
            * Its duration is zero
            * Its description is `?`
            * Its alias ends with a `?`
        """
        return (
            self.has_flag(self.FLAG_IGNORED) or self.hours == 0
        )

    @ignored.setter
    def ignored(self, value):
        """
        Set the ignored flag if the `value` it is set to evaluates to True,
        remove it otherwise.
        """
        self._add_or_remove_flag(self.FLAG_IGNORED, value)


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
        return dict(self.items()).__repr__()

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

    def __add__(self, other):
        new_collection = EntriesCollection(parser=self.parser)

        for entries_collection in (self, other):
            for entry_date, entries in entries_collection.items():
                for entry in entries:
                    new_collection.add(entry_date, entry)

        return new_collection

    def is_top_down(self):
        return is_top_down(self.lines)

    @synchronized
    def add_entry(self, date, entry):
        """
        Add the given entry to the textual representation.
        """
        in_date = False
        insert_at = 0

        for (lineno, line) in enumerate(self.lines):
            # Search for the date of the entry
            if isinstance(line, DateLine) and line.date == date:
                in_date = True
                # Insert here if there is no existing Entry for this date
                insert_at = lineno
                continue

            if in_date:
                if isinstance(line, Entry):
                    insert_at = lineno
                elif isinstance(line, DateLine):
                    break

        self.lines.insert(insert_at + 1, entry)

        # If there's no other Entry in the current date, add a blank line
        # between the date and the entry
        if not isinstance(self.lines[insert_at], Entry):
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
            if not isinstance(line, Entry) or line not in entries
        ])

    def add(self, date, entry):
        self[date].append(entry)

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

        for lineno, line in enumerate(self.lines, 1):
            if isinstance(line, DateLine):
                current_date = line.date
                self[current_date] = self.default_factory(self, line.date)
            elif isinstance(line, Entry):
                if len(self[current_date]) > 0:
                    line.previous_entry = self[current_date][-1]
                    self[current_date][-1].next_entry = line

                start_time = line.get_start_time()
                if start_time and line.duration[1] and line.duration[1] <= start_time:
                    line_str = " ".join(line._text).strip()
                    raise EntriesCollectionValidationError(
                        "Error at line {lineno} of your timesheet:\n\n\t{line}"
                        "\n\nThe entry cannot go back in time. If you're trying "
                        "to create an entry that spans on 2 days, please create "
                        "an entry on 2 separate days.".format(
                            lineno=lineno, line=line_str
                        )
                    )

                self[current_date].append(line)

    def to_lines(self):
        """
        Return a list of strings, each string being a line of the entries
        collection (dates, entries and text).
        """
        return [self.parser.to_text(line) for line in self.lines]

    def filter(self, date=None, regroup=False, ignored=None, pushed=None, unmapped=None, current_workday=None):
        """
        Return the entries as a dict of {:class:`datetime.date`: :class:`~taxi.timesheet.lines.Entry`}
        items.

        `date` can either be a single :class:`datetime.date` object to filter only entries from the given date,
        or a tuple of :class:`datetime.date` objects representing `(from, to)`. `filter_callback` is a function that,
        given a :class:`~taxi.timesheet.lines.Entry` object, should return True to include that line, or False to
        exclude it. If `regroup` is set to True, similar entries (ie. having the same
        :meth:`~taxi.timesheet.lines.Entry.hash`) will be regrouped intro a single
        :class:`~taxi.timesheet.entry.AggregatedTimesheetEntry`.
        """
        def entry_filter(entry_date, entry):
            if ignored is not None and entry.ignored != ignored:
                return False

            if pushed is not None and entry.pushed != pushed:
                return False

            if unmapped is not None and entry.mapped == unmapped:
                return False

            if current_workday is not None:
                today = datetime.date.today()
                yesterday = date_utils.get_previous_working_day(today)
                is_current_workday = entry_date in (today, yesterday) and entry_date.strftime('%w') not in [6, 0]

                if current_workday != is_current_workday:
                    return False

            return True

        # Date can either be a single date (only 1 day) or a tuple for a
        # date range
        if date is not None and not isinstance(date, tuple):
            date = (date, date)

        filtered_entries = collections.defaultdict(list)

        for (entries_date, entries) in self.items():
            if (date is not None and (
                    (date[0] is not None and entries_date < date[0])
                    or (date[1] is not None and entries_date > date[1]))):
                continue

            entries_for_date = []

            if regroup:
                # This is a mapping between entries hashes and their
                # position in the entries_for_date list
                aggregated_entries = {}
                id = 0

                for entry in entries:
                    if not entry_filter(entries_date, entry):
                        continue

                    # Common case: the entry is not yet referenced in the
                    # aggregated_entries dict
                    if entry.hash not in aggregated_entries:
                        # In that case, put it normally in the entries_for_date
                        # list. It will get replaced by an AggregatedEntry
                        # later if necessary
                        entries_for_date.append(entry)
                        aggregated_entries[entry.hash] = id
                        id += 1
                    else:
                        # Get the first occurence of the entry in the
                        # entries_for_date list
                        existing_entry = entries_for_date[
                            aggregated_entries[entry.hash]
                        ]

                        # The entry could already have been replaced by an
                        # AggregatedEntry if there's more than 2 occurences
                        if isinstance(existing_entry, Entry):
                            # Create the AggregatedEntry, put the first
                            # occurence of Entry in it and the current one
                            aggregated_entry = AggregatedTimesheetEntry()
                            aggregated_entry.entries.append(existing_entry)
                            aggregated_entry.entries.append(entry)
                            entries_for_date[
                                aggregated_entries[entry.hash]
                            ] = aggregated_entry
                        else:
                            # The entry we found is already an
                            # AggregatedEntry, let's just append the
                            # current entry to it
                            aggregated_entry = existing_entry
                            aggregated_entry.entries.append(entry)
            else:
                entries_for_date = [
                    entry for entry in entries if entry_filter(entries_date, entry)
                ]

            if entries_for_date:
                filtered_entries[entries_date].extend(entries_for_date)

        return filtered_entries

    def append_text(self, lines):
        textlines = [TextLine(line) for line in lines]
        self.lines += textlines


class EntriesList(list):
    """
    The EntriesList class is a classic list that synchronizes its data with the
    textual representation from the bound entries collection.
    """
    def __init__(self, entries_collection, date):
        super(EntriesList, self).__init__()

        self.entries_collection = entries_collection
        self.date = date

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
