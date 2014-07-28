from .entry import EntriesCollection


class Timesheet(object):
    def __init__(self, entries=None, mappings=None, date_format='%d.%m.%Y'):
        self.entries = entries if entries is not None else EntriesCollection()
        self.mappings = mappings if mappings is not None else {}
        self.date_format = date_format

    def get_entries(self, date=None, exclude_ignored=False, regroup=False):
        if date is not None:
            return self.entries[date]

        return self.entries

    def get_ignored_entries(self, date=None):
        pass

    def stop_running_entry(self, date, end_time=None, description=None):
        pass


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
