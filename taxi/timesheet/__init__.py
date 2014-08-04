from collections import defaultdict
import datetime
import os

from ..utils import date as date_utils
from .entry import EntriesCollection


class Timesheet(object):
    def __init__(self, entries=None, mappings=None):
        self.entries = entries if entries is not None else EntriesCollection()
        self.mappings = mappings if mappings is not None else {}

    def get_filtered_entries(self, date=None, filter_callback=None):
        # Date can either be a single date (only 1 day) or a tuple for a
        # date range
        if date is not None and not isinstance(date, tuple):
            date = (date, date)

        filtered_entries = defaultdict(list)

        for (entries_date, entries) in self.entries.iteritems():
            if (date is not None
                    and (entries_date < date[0] or entries_date > date[1])):
                continue

            if filter_callback is None:
                filtered_entries[entries_date] = entries
            else:
                filtered_entries[entries_date] = [
                    entry for entry in entries if filter_callback(entry)
                ]

        return filtered_entries

    def get_entries(self, date=None, exclude_ignored=False,
                    exclude_local=False, regroup=False):
        # TODO regroup
        def entry_filter(entry):
            return (not (exclude_ignored and entry.is_ignored())
                    and not (exclude_local and self.is_alias_local(entry.alias)))

        return self.get_filtered_entries(date, entry_filter)

    def get_ignored_entries(self, date=None):
        return self.get_filtered_entries(date, lambda e: e.is_ignored())

    def get_local_entries(self, date=None):
        return self.get_filtered_entries(
            date, lambda e: self.is_alias_local(e.alias)
        )

    def is_alias_local(self, alias):
        return alias in self.mappings and self.mappings[alias] is None

    def get_non_current_workday_entries(self):
        non_workday_entries = {}

        today = datetime.date.today()
        yesterday = date_utils.get_previous_working_day(today)

        for (date, date_entries) in self.entries.iteritems():
            if date not in (today, yesterday) or date.strftime('%w') in [6, 0]:
                if date_entries:
                    non_workday_entries[date] = date_entries

        return non_workday_entries

    def continue_entry(self, date, end_time, description=None):
        entry = self.entries[date][-1]
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
            if cur_date.weekday() in auto_fill_days:
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


class TimesheetFile(object):
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self, create=True):
        try:
            with open(self.file_path, 'r') as timesheet_file:
                return timesheet_file.read()
        except IOError:
            if create:
                open(self.file_path, 'w').close()
                return ''
            else:
                raise

    def write(self, entries):
        with open(self.file_path, 'w') as timesheet_file:
            for line in entries.to_lines():
                timesheet_file.write(u'%s\n' % line)


class Mapping(object):
    def __init__(self, alias, project_id, activity_id):
        self.alias = alias
        self.project_id = project_id
        self.activity_id = activity_id
