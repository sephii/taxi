from __future__ import unicode_literals

import codecs
import datetime
import os
from functools import reduce

import six

from ..exceptions import NoActivityInProgressError, ParseError
from ..utils import file as file_utils
from ..utils.structures import OrderedSet
from .entry import EntriesCollection
from .parser import TimesheetParser


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


@six.python_2_unicode_compatible
class Timesheet(object):
    """
    A timesheet is a link between an entries collection and a file.
    """
    def __init__(self, entries=None):
        self.entries = entries if entries is not None else EntriesCollection(TimesheetParser())
        self.file = None

    def __str__(self):
        return '\n'.join(self.entries.to_lines())

    @classmethod
    def load(cls, file_path, parser=None):
        """
        Load the timesheet file located in `file_path`. If `parser` is not set,
        :class:`~taxi.timesheet.parser.TimesheetParser` will be used. If the file doesn't exist, an empty timesheet
        will be returned. If the file exists and its contents are not a valid timesheet,
        :exc:`~taxi.timesheet.parser.ParseError` will be raised.
        """
        if not parser:
            parser = TimesheetParser()

        try:
            with codecs.open(file_path, 'r', 'utf-8') as timesheet_file:
                contents = timesheet_file.read()
        except IOError:
            contents = ''

        entries = EntriesCollection(parser, contents)

        timesheet = cls(entries)
        timesheet.file_path = file_path

        return timesheet

    def save(self, file_path=None):
        """
        Save the contents of the timesheet to the given `file_path`. If `file_path` is not set, the timesheet will be
        saved to the same file as it was loaded from.
        """
        file_path = file_path or self.file_path

        if not file_path:
            raise ValueError("save() needs a `file_path` parameter since the timesheet wasn't loaded from a file")

        try:
            open(file_path, 'r').close()
        except IOError:
            try:
                os.makedirs(os.path.split(file_path)[0])
            except OSError:
                pass

        with codecs.open(file_path, 'w', 'utf-8') as timesheet_file:
            timesheet_file.writelines([line + '\n' for line in self.entries.to_lines()])

    def get_hours(self, **kwargs):
        """
        Return the total hours of the entries filtered by the given `kwargs`, which are the same as
        :meth:`~taxi.timesheet.entry.EntriesCollection.filter`.
        """
        date_entries = self.entries.filter(**kwargs)
        return sum(sum(entry.hours for entry in entries) for entries in date_entries.values())

    def continue_entry(self, date, end_time, description=None):
        """
        Find the in-progress entry for the given date (ie. the last entry that has an empty end time) and set its end
        time and optionally its description to the given values. `end_time` should be a :class:`datetime.time` object.
        :exc:`~taxi.exceptions.NoActivityInProgressError` will be raised if there's no entry in the given date, if the
        last entry doesn't have a start time, or if the last entry already has an end time.
        """
        try:
            entry = self.entries[date][-1]
        except IndexError:
            raise NoActivityInProgressError()

        if not entry.in_progress:
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
    def __init__(self, timesheets=None):
        self.timesheets = timesheets if timesheets else []

    def __repr__(self):
        return '<TimesheetCollection: %s>' % (self.timesheets.__repr__())

    def __getitem__(self, key):
        return self.timesheets[key]

    def _timesheets_callback(self, callback):
        """
        Call a method on all the timesheets, aggregate the return values in a
        list and return it.
        """
        def call(*args, **kwargs):
            return_values = []

            for timesheet in self.timesheets:
                attr = getattr(timesheet, callback)

                if callable(attr):
                    result = attr(*args, **kwargs)
                else:
                    result = attr

                return_values.append(result)

            return return_values

        return call

    @property
    def entries(self):
        """
        Return the entries (as a {date: entries} dict) of all timesheets in the
        collection.
        """
        entries_list = self._timesheets_callback('entries')()

        return reduce(lambda x, y: x + y, entries_list)

    def get_hours(self, **kwargs):
        return sum(self._timesheets_callback('get_hours')(**kwargs))

    def __getattr__(self, name):
        """
        Proxy all methods not defined here to the timesheets.
        """
        if hasattr(Timesheet, name):
            return self._timesheets_callback(name)
        else:
            raise AttributeError(name)


def get_timesheet_collection(file_pattern, nb_previous_files, parser):
    timesheet_collection = TimesheetCollection()
    timesheet_files = get_files(file_pattern, nb_previous_files)

    for file_path in timesheet_files:
        try:
            timesheet = Timesheet.load(file_path, parser=parser)
        except ParseError as e:
            e.file = file_path
            raise

        timesheet_collection.timesheets.append(timesheet)

    # Fix `add_date_to_bottom` attribute of timesheet entries based on
    # previous timesheets. When a new timesheet is started it won't have
    # any direction defined, so we take the one from the previous
    # timesheet, if any
    if parser.add_date_to_bottom is None:
        previous_timesheet = None
        for timesheet in reversed(timesheet_collection.timesheets):
            if previous_timesheet:
                previous_timesheet_top_down = previous_timesheet.entries.is_top_down()

                if previous_timesheet_top_down is not None:
                    timesheet.entries.parser.add_date_to_bottom = previous_timesheet_top_down
            previous_timesheet = timesheet

    return timesheet_collection


def get_files(file_pattern, nb_previous_files, from_date=None):
    date_units = ['m', 'Y']
    smallest_unit = None

    if not from_date:
        from_date = datetime.date.today()

    for date in date_units:
        if '%%%s' % date in file_pattern:
            smallest_unit = date
            break

    if smallest_unit is None:
        return OrderedSet([file_pattern])

    files = OrderedSet()
    file_date = from_date
    for i in six.moves.xrange(0, nb_previous_files + 1):
        files.add(file_utils.expand_date(file_pattern, file_date))

        if smallest_unit == 'm':
            if file_date.month == 1:
                file_date = file_date.replace(day=1,
                                              month=12,
                                              year=file_date.year - 1)
            else:
                file_date = file_date.replace(day=1,
                                              month=file_date.month - 1)
        elif smallest_unit == 'Y':
            file_date = file_date.replace(day=1, year=file_date.year - 1)

    return files
