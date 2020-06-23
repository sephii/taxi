import codecs
import datetime
import enum
import os
import re
from collections import defaultdict
from functools import reduce

from ..exceptions import NoActivityInProgressError, ParseError, StopInThePastError
from ..utils import file as file_utils
from ..utils.date import months_ago
from ..utils.structures import OrderedSet
from .entry import EntriesCollection
from .parser import TimesheetParser


def round_to(start_time, end_time, precision_minutes):
    """
    Return the duration between `start_time` and `end_time`
    :class:`datetime.time` objects, rounded to `precision_minutes` minutes.
    """
    def to_seconds(time):
        return time.second + time.minute * 60 + time.hour * 60 * 60

    precision_seconds = precision_minutes * 60
    difference = to_seconds(end_time) - to_seconds(start_time)
    needs_rounding = difference % precision_seconds > 0
    rounded_difference = ((difference // precision_seconds) + 1) * precision_seconds if needs_rounding else difference

    return (
        datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(seconds=rounded_difference)
    ).time()


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
    def load(cls, file_path, parser=None, initial=''):
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
            if callable(initial):
                contents = initial()
            else:
                contents = initial

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

    def continue_entry(self, date, end_time, rounded_to_minutes, description=None):
        """
        Find the in-progress entry for the given date (ie. the last entry that has an empty end time) and set its end
        time and optionally its description to the given values. `end_time` should be a :class:`datetime.time` object.
        :exc:`~taxi.exceptions.NoActivityInProgressError` will be raised if there's no entry in the given date, if the
        last entry doesn't have a start time, or if the last entry already has an end time.
        """
        try:
            entry = self.entries[date][-1]
        except IndexError:
            raise NoActivityInProgressError("You don't have any activity in progress for today")

        if not entry.in_progress:
            raise NoActivityInProgressError("You don't have any activity in progress for today")

        if entry.get_start_time() > end_time:
            raise StopInThePastError("You are trying to stop an activity in the future")

        entry.duration = (entry.duration[0], round_to(
            entry.get_start_time(),
            end_time,
            precision_minutes=rounded_to_minutes
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

    def get_popular_aliases(self, limit=5):
        """
        Return a list of 2-tuples `(alias, usage_count)`, sorted by `usage_count` of aliases used in this timesheet.
        Only the top `limit` aliases are returned. If `limit` is left empty, all aliases are returned.
        """
        aliases_count = defaultdict(int)

        for entries_list in self.entries.values():
            for entry in entries_list:
                aliases_count[entry.alias] += 1

        sorted_aliases_count = sorted(aliases_count.items(), key=lambda item: item[1], reverse=True)

        if limit:
            return sorted_aliases_count[:limit]
        else:
            return sorted_aliases_count


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

    def __iter__(self):
        return self.timesheets.__iter__()

    def __getattr__(self, name):
        """
        Proxy all methods not defined here to the timesheets.
        """
        if hasattr(Timesheet, name):
            return self._timesheets_callback(name)
        else:
            raise AttributeError(name)

    def _timesheets_callback(self, callback):
        """
        Call a method on all the timesheets, aggregate the return values in a
        list and return it.
        """
        def call(*args, **kwargs):
            return_values = []

            for timesheet in self:
                attr = getattr(timesheet, callback)

                if callable(attr):
                    result = attr(*args, **kwargs)
                else:
                    result = attr

                return_values.append(result)

            return return_values

        return call

    @classmethod
    def load(cls, file_pattern, nb_previous_files=1, parser=None):
        """
        Load a collection of timesheet from the given `file_pattern`. `file_pattern` is a path to a timesheet file that
        will be expanded with :func:`datetime.date.strftime` and the current date. `nb_previous_files` is the number of
        other timesheets to load, depending on `file_pattern` this will result in either the timesheet from the
        previous month or from the previous year to be loaded. If `parser` is not set, a default
        :class:`taxi.timesheet.parser.TimesheetParser` will be used.
        """
        if not parser:
            parser = TimesheetParser()

        timesheet_files = cls.get_files(file_pattern, nb_previous_files)
        timesheet_collection = cls()

        for file_path in timesheet_files:
            try:
                timesheet = Timesheet.load(
                    file_path, parser=parser, initial=lambda: timesheet_collection.get_new_timesheets_contents()
                )
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
            for timesheet in timesheet_collection.timesheets:
                if previous_timesheet:
                    previous_timesheet_top_down = previous_timesheet.entries.is_top_down()

                    if previous_timesheet_top_down is not None:
                        timesheet.entries.parser.add_date_to_bottom = previous_timesheet_top_down
                previous_timesheet = timesheet

        return timesheet_collection

    @classmethod
    def get_files(cls, file_pattern, nb_previous_files, from_date=None):
        """
        Return an :class:`~taxi.utils.structures.OrderedSet` of file paths expanded from `filename`, with a maximum of
        `nb_previous_files`. See :func:`taxi.utils.file.expand_date` for more information about filename expansion. If
        `from_date` is set, it will be used as a starting date instead of the current date.
        """
        if not from_date:
            from_date = datetime.date.today()

        Resolution = enum.IntEnum("Resolution", "DAY WEEK MONTH YEAR")
        resolutions = {
            'a': Resolution.WEEK,
            'A': Resolution.WEEK,
            'w': Resolution.WEEK,
            'd': Resolution.DAY,
            'b': Resolution.MONTH,
            'B': Resolution.MONTH,
            'm': Resolution.MONTH,
            'y': Resolution.YEAR,
            'Y': Resolution.YEAR,
            'j': Resolution.DAY,
            'U': Resolution.WEEK,
            'W': Resolution.WEEK,
            'V': Resolution.WEEK,
            'u': Resolution.DAY,
        }
        used_units = re.findall(r'%([a-zA-Z])', file_pattern)
        unknown_units = set(used_units) - set(resolutions.keys())

        if unknown_units:
            raise ValueError(
                "Unsupported units used in file pattern: {}".format(
                    ", ".join("%{}".format(unit) for unit in unknown_units)
                )
            )

        if not used_units:
            return OrderedSet([file_utils.expand_date(file_pattern, from_date)])

        resolution = min(resolutions[res] for res in used_units)
        files = OrderedSet()

        for i in range(nb_previous_files, -1, -1):
            if resolution == Resolution.MONTH:
                file_date = months_ago(from_date, i)
            elif resolution == Resolution.YEAR:
                file_date = from_date.replace(day=1, year=from_date.year - i)
            elif resolution == Resolution.DAY:
                file_date = from_date - datetime.timedelta(days=i)
            elif resolution == Resolution.WEEK:
                file_date = from_date - datetime.timedelta(days=i * 7)

            files.add(file_utils.expand_date(file_pattern, file_date))

        return files

    def get_new_timesheets_contents(self):
        """
        Return the initial text to be inserted in new timesheets.
        """
        popular_aliases = self.get_popular_aliases()
        template = ['# Recently used aliases:']

        if popular_aliases:
            contents = '\n'.join(template + ['# ' + entry for entry, usage in popular_aliases])
        else:
            contents = ''

        return contents

    @property
    def entries(self):
        """
        Return the entries (as a {date: entries} dict) of all timesheets in the
        collection.
        """
        entries_list = self._timesheets_callback('entries')()

        return reduce(lambda x, y: x + y, entries_list)

    def get_hours(self, **kwargs):
        """
        Return the total hours of all the timesheet in this collection.
        """
        return sum(self._timesheets_callback('get_hours')(**kwargs))

    def get_popular_aliases(self, *args, **kwargs):
        """
        Return the aggregated results of :meth:`Timesheet.get_popular_aliases`.
        """
        aliases_count_total = defaultdict(int)
        aliases_counts = self._timesheets_callback('get_popular_aliases')(*args, **kwargs)

        for aliases_count in aliases_counts:
            for alias, count in aliases_count:
                aliases_count_total[alias] += count

        sorted_aliases_count_total = sorted(aliases_count_total.items(), key=lambda item: item[1], reverse=True)

        return sorted_aliases_count_total

    def latest(self):
        """
        Return the latest timesheet (ie. the most recent one) of this collection.
        """
        return self[-1]

    def earliest(self):
        """
        Return the earliest timesheet (ie. the oldest one) of this collection.
        """
        return self[0]
