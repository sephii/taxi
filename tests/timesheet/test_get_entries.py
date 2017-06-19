from taxi.timesheet import EntriesCollection, Timesheet
from taxi.timesheet.parser import TimesheetParser
from . import create_timesheet


def test_get_entries_excluding_unmapped_excludes_unmapped():
    contents = "10.10.2012\nbaz 2 Foo"
    t = create_timesheet(contents)
    assert len(t.entries.filter(unmapped=False)) == 0


def test_get_entries_excluding_unmapped_includes_mapped():
    contents = "10.10.2012\nfoo 2 Foo"
    t = create_timesheet(contents)
    assert len(t.entries.filter(unmapped=False)) == 1


def test_get_entries_excluding_ignored_excludes_ignored():
    contents = "10.10.2012\n? foo 2 Foo"
    t = create_timesheet(contents)
    assert len(t.entries.filter(ignored=False)) == 0


def test_get_entries_excluding_ignored_includes_non_ignored():
    contents = "10.10.2012\nfoo 2 Foo"
    t = create_timesheet(contents)
    assert len(list(t.entries.filter(ignored=False).values())[0]) == 1


def test_get_entries_excluding_pushed_excludes_pushed():
    contents = """01.04.2013
foo 2 bar
= bar 0900-1000 bar
foo 1 bar"""
    entries = EntriesCollection(TimesheetParser(), contents)
    timesheet = Timesheet(entries)
    timesheet_entries = timesheet.entries.filter(pushed=False)

    assert len(list(timesheet_entries.values())[0]) == 2
