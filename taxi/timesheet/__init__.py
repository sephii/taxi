from collections import defaultdict
import datetime

from .entry import EntriesCollection


class Timesheet(object):
    def __init__(self, entries=None, mappings=None, date_format='%d.%m.%Y'):
        self.entries = entries if entries is not None else EntriesCollection()
        self.mappings = mappings if mappings is not None else {}
        self.date_format = date_format

    def get_entries(self, date=None, exclude_ignored=False, regroup=False):
        if date is not None:
            return {date: self.entries[date]}

        return self.entries

    def get_ignored_entries(self, date=None):
        entries = self.get_entries(date)
        ignored_entries = defaultdict(list)

        for (date, entries) in entries.iteritems():
            for entry in entries:
                if entry.is_ignored():
                    ignored_entries[date].append(entry)

        return ignored_entries

    def continue_entry(self, date, end_time, description=None):
        entry = self.entries[date][-1]
        entry.duration = (entry.duration[0], self.round_to_quarter(
            entry.duration[0],
            end_time
        ))

        if description is not None:
            entry.description = description

    def stop_running_entry(self, date, end_time=None, description=None):
        pass

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

        with open(self.file_path, 'r') as timesheet_file:
            self.text = timesheet_file.read()


class Mapping(object):
    def __init__(self, alias, project_id, activity_id):
        self.alias = alias
        self.project_id = project_id
        self.activity_id = activity_id
