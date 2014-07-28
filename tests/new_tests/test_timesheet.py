import datetime

from taxi.timesheet import Timesheet
from taxi.timesheet.entry import EntriesCollection


def test_empty_timesheet():
    timesheet = Timesheet()
    assert len(timesheet.entries) == 0


def test_timesheet_with_entries():
    entries = EntriesCollection("""10.10.2014\nfoo 2 bar\n11.10.2014\nfoo 1 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.entries) == 2


def test_timesheet_get_entries():
    entries = EntriesCollection("""10.10.2014\nfoo 2 bar\n11.10.2014\nfoo 1 bar""")

    timesheet = Timesheet(entries)
    assert len(timesheet.get_entries(datetime.date(2014, 10, 10))) == 1
