from __future__ import unicode_literals

import codecs
from collections import defaultdict
import datetime
import os

import six

from ..aliases import aliases_database
from ..utils import date as date_utils
from .entry import AggregatedTimesheetEntry, EntriesCollection
from .parser import EntryLine, TimesheetParser


def is_entry_ignored(entry):
    """
    Return `True` if the given `entry` has the entry flag or is not in the aliases database.
    """
    return entry.ignored or entry.alias not in aliases_database


def round_to_quarter(start_time, end_time):
    """
    Return the duration between `start_time` and `end_time` :class:`datetime.time` objects, rounded to 15 minutes.
    """
    # We don't care about the date (only about the time) but Python
    # can substract only datetime objects, not time ones
    today = datetime.date.today()
    start_date = datetime.datetime.combine(today, start_time)
    end_date = datetime.datetime.combine(today, end_time)

    difference_minutes = (end_date - start_date).seconds / 60
    remainder = difference_minutes % 15
    # Round up
    difference_minutes += 15 - remainder if remainder > 0 else 0

    return (
        start_date + datetime.timedelta(minutes=difference_minutes)
    ).time()


class Timesheet(object):
    """
    A timesheet is a link between an entries collection and a file.
    """
    def __init__(self, entries=None, file=None):
        self.entries = entries if entries is not None else EntriesCollection(TimesheetParser())
        self.file = file

    def get_filtered_entries(self, date=None, filter_callback=None, regroup=False):
        """
        Return the timesheet entries as a dict of {:class:`datetime.date`: :class:`~taxi.timesheet.lines.EntryLine`}
        items.

        `date` can either be a single :class:`datetime.date` object to filter only entries from the given date,
        or a tuple of :class:`datetime.date` objects representing `(from, to)`. `filter_callback` is a function that,
        given a :class:`~taxi.timesheet.lines.EntryLine` object, should return True to include that line, or False to
        exclude it. If `regroup` is set to True, similar entries (ie. having the same
        :meth:`~taxi.timesheet.lines.EntryLine.hash`) will be regrouped intro a single
        :class:`~taxi.timesheet.entry.AggregatedTimesheetEntry`.
        """
        # Date can either be a single date (only 1 day) or a tuple for a
        # date range
        if date is not None and not isinstance(date, tuple):
            date = (date, date)

        filtered_entries = defaultdict(list)

        for (entries_date, entries) in six.iteritems(self.entries):
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
                    if (filter_callback is not None
                            and not filter_callback(entry)):
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
                        if isinstance(existing_entry, EntryLine):
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
                if filter_callback is None:
                    entries_for_date = entries
                else:
                    entries_for_date = [
                        entry for entry in entries if filter_callback(entry)
                    ]

            filtered_entries[entries_date].extend(entries_for_date)

        return filtered_entries

    def get_entries(self, date=None, exclude_ignored=False,
                    exclude_unmapped=False, exclude_pushed=False,
                    regroup=False):
        """
        Return all entries from this timesheet as a dict of `{date: entries}` where `date` is a :class:`datetime.date`
        object and `entries` is a list of :class:`taxi.timesheet.lines.EntryLine` instances. `date` can either be a
        :class:`datetime.date` object or a 2-tuple of :class:`datetime.date` objects to only include entries between
        the 2 given dates.

        The `exclude_ignored`, `exclude_unmapped` and `exclude_pushed` parameters can be set to exclude certain entries
        from the result. If `regroup` is `True`, similar entries (sharing the same alias and description) will be
        regrouped as single entries.

        This method is a helper to :meth:`get_filtered_entries`. If you need a more granular filter function, use
        :meth:`get_filtered_entries` instead.
        """
        def entry_filter(entry):
            return (not (exclude_ignored and entry.ignored)
                    and (not exclude_unmapped
                         or entry.alias in aliases_database)
                    and (not exclude_pushed
                         or not entry.pushed))

        return self.get_filtered_entries(date, entry_filter, regroup)

    def get_hours(self, **kwargs):
        """
        Return the total hours of the entries filtered by the given `kwargs`, which are the same as
        :meth:`get_entries`.
        """
        date_entries = self.get_entries(**kwargs)
        return sum(sum(entry.hours for entry in entries) for entries in date_entries.values())

    def get_ignored_entries(self, date=None, exclude_pushed=True):
        """
        Return all ignored entries for this timesheet. See :meth:`get_filtered_entries` for the type of the `date`
        parameter. If `exclude_pushed` is `False`, pushed entries will be included.
        """
        def entry_filter(entry):
            return is_entry_ignored(entry) and not (exclude_pushed and entry.pushed)

        return self.get_filtered_entries(date, entry_filter)

    def get_non_current_workday_entries(self):
        """
        Return a list of :class:`~taxi.timesheet.lines.EntryLine` objects that are not considered as being in the
        "current workday". The current workday is either the current day or the day before the current day (which will
        be Friday if the current day is Monday).
        """
        non_workday_entries = defaultdict(list)

        today = datetime.date.today()
        yesterday = date_utils.get_previous_working_day(today)

        for (date, date_entries) in six.iteritems(self.entries):
            if date not in (today, yesterday) or date.strftime('%w') in [6, 0]:
                for entry in date_entries:
                    if not is_entry_ignored(entry) and not entry.pushed:
                        non_workday_entries[date].append(entry)

        return non_workday_entries

    def continue_entry(self, date, end_time, description=None):
        """
        Find the in-progress entry for the given date (ie. the last entry that has an empty end time) and set its end
        time and optionally its description to the given values. `end_time` should be a :class:`datetime.time` object.
        :exc:`NoActivityInProgressError` will be raised if there's no entry in the given date, if the last entry
        doesn't have a start time, or if the last entry already has an end time.
        """
        try:
            entry = self.entries[date][-1]
        except IndexError:
            raise NoActivityInProgressError()

        if (not isinstance(entry.duration, tuple)
                or entry.duration[1] is not None):
            raise NoActivityInProgressError()

        entry.duration = (entry.duration[0], self.round_to_quarter(
            entry.duration[0],
            end_time
        ))

        if description is not None:
            entry.description = description

    def prefill(self, auto_fill_days, limit=None):
        """
        Add missing dates to the timesheet with respect to `auto_fill_days`, which should be a list of integers from
        0-6, 0 being Monday and 6 Sunday. If `limit` is set, only dates up to the `limit` :class:`~datetime.date` will
        be inserted.
        """
        today = datetime.date.today()

        if limit is None:
            limit = today

        if not self.entries:
            cur_date = datetime.date(today.year, today.month, 1)
        else:
            cur_date = max([date for date in self.entries.keys()])
            cur_date += datetime.timedelta(days=1)

        while cur_date <= limit:
            if (cur_date.weekday() in auto_fill_days and
                    cur_date not in self.entries):
                self.entries[cur_date] = []

            cur_date = cur_date + datetime.timedelta(days=1)


class TimesheetCollection:
    """
    This is a collection of timesheets. It's basically a proxy class that calls
    methods on all timesheets it contains.
    """
    def __init__(self):
        self.timesheets = []

    def __repr__(self):
        return '<TimesheetCollection: %s>' % (self.timesheets.__repr__())

    def _timesheets_callback(self, callback):
        """
        Call a method on all the timesheets, aggregate the return values in a
        list and return it.
        """
        def call(*args, **kwargs):
            return_values = []

            for timesheet in self.timesheets:
                return_values.append(
                    getattr(timesheet, callback)(*args, **kwargs)
                )

            return return_values

        return call

    def get_entries(self, *args, **kwargs):
        """
        Return the entries (as a {date: entries} dict) of all timesheets in the
        collection.
        """
        entries_list = self._timesheets_callback(
            'get_entries')(*args, **kwargs)
        entries = {}

        for entries_dict in entries_list:
            entries.update(entries_dict)

        return entries

    def get_ignored_entries(self, *args, **kwargs):
        """
        Return the ignored entries (as a {date: entries} dict) of all
        timesheets in the collection.
        """
        entries_list = self._timesheets_callback(
            'get_ignored_entries')(*args, **kwargs)
        entries = {}

        for entries_dict in entries_list:
            entries.update(entries_dict)

        return entries

    def get_non_current_workday_entries(self, *args, **kwargs):
        """
        Return the non current workday entries (as a {date: entries} dict) of
        all timesheets in the collection.
        """
        entries_list = self._timesheets_callback(
            'get_non_current_workday_entries')(*args, **kwargs)
        entries = {}

        for entries_dict in entries_list:
            entries.update(entries_dict)

        return entries

    def get_hours(self, **kwargs):
        return sum(self._timesheets_callback('get_hours')(**kwargs))

    def __getattr__(self, name):
        """
        Proxy all methods not defined here to the timesheets.
        """
        if hasattr(Timesheet, name):
            return self._timesheets_callback(name)
        else:
            raise AttributeError()


class TimesheetFile(object):
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        with codecs.open(self.file_path, 'r', 'utf-8') as timesheet_file:
            return timesheet_file.read()

    def write(self, entries):
        try:
            open(self.file_path, 'r').close()
        except IOError:
            try:
                os.makedirs(os.path.split(self.file_path)[0])
            except OSError:
                pass

        with codecs.open(self.file_path, 'w', 'utf-8') as timesheet_file:
            for line in entries.to_lines():
                timesheet_file.write('%s\n' % line)


class NoActivityInProgressError(Exception):
    pass
