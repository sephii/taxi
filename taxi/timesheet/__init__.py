from __future__ import unicode_literals

import codecs
from collections import defaultdict
import datetime
import os

import six

from ..aliases import aliases_database
from ..utils import date as date_utils
from .entry import AggregatedTimesheetEntry, EntriesCollection, TimesheetEntry


class Timesheet(object):
    def __init__(self, entries=None, file=None):
        self.entries = entries if entries is not None else EntriesCollection()
        self.file = file

    def get_filtered_entries(self, date=None, filter_callback=None,
                             regroup=False):
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
                        if isinstance(existing_entry, TimesheetEntry):
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
                    exclude_unmapped=False, regroup=False):
        def entry_filter(entry):
            return (not (exclude_ignored and entry.is_ignored())
                    and (not exclude_unmapped
                         or entry.alias in aliases_database))

        return self.get_filtered_entries(date, entry_filter, regroup)

    def get_ignored_entries(self, date=None):
        def entry_filter(entry):
            return self.is_entry_ignored(entry)

        return self.get_filtered_entries(date, entry_filter)

    def get_non_current_workday_entries(self):
        non_workday_entries = defaultdict(list)

        today = datetime.date.today()
        yesterday = date_utils.get_previous_working_day(today)

        for (date, date_entries) in six.iteritems(self.entries):
            if date not in (today, yesterday) or date.strftime('%w') in [6, 0]:
                for entry in date_entries:
                    if not self.is_entry_ignored(entry):
                        non_workday_entries[date].append(entry)

        return non_workday_entries

    def is_entry_ignored(self, entry):
        return entry.is_ignored() or entry.alias not in aliases_database

    def continue_entry(self, date, end_time, description=None):
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

    @staticmethod
    def round_to_quarter(start_time, end_time):
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


class TimesheetCollection:
    """
    This is a collection of timesheets. It's basically a proxy class that calls
    methods on all timesheets it contains.
    """
    def __init__(self):
        self.timesheets = []

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
