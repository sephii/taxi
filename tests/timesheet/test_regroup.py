import datetime

from . import create_timesheet


def test_regroup_doesnt_regroup_entries_with_different_alias():
    contents = """01.04.2013
foo 2 bar
bar 2 bar"""

    t = create_timesheet(contents)
    entries = list(t.entries.filter(regroup=True).values())[0]
    assert len(entries) == 2


def test_regroup_doesnt_regroup_entries_with_different_description():
    contents = """01.04.2013
foo 2 bar
foo 2 baz"""

    t = create_timesheet(contents)
    entries = list(t.entries.filter(regroup=True).values())[0]
    assert len(entries) == 2


def test_regroup_regroups_entries_with_same_alias_and_description():
    contents = """01.04.2013
foo 2 bar
foo 3 bar
bar 1 barz"""

    t = create_timesheet(contents)
    entries = list(t.entries.filter(regroup=True).values())[0]
    assert len(entries) == 2


def test_regroup_adds_time():
    contents = """01.04.2013
foo 2 bar
foo 3 bar"""

    t = create_timesheet(contents)
    entries = list(t.entries.filter(regroup=True).values())[0]
    assert entries[0].hours == 5


def test_regroup_adds_time_with_start_and_end_time():
    contents = """01.04.2013
foo 2 bar
foo 0900-1000 bar"""

    t = create_timesheet(contents)
    entries = list(t.entries.filter(regroup=True).values())[0]
    assert entries[0].hours == 3


def test_regroup_doesnt_regroup_ignored_entries_with_non_ignored_entries():
    contents = """01.04.2013
foo 2 bar
? foo 3 test"""

    t = create_timesheet(contents)
    entries = list(t.entries.filter(regroup=True).values())[0]
    assert len(entries) == 2


def test_regroup_regroups_entries_with_partial_time():
    contents = """01.04.2013
foo 2 bar
foo 0800-0900 bar
bar -1000 bar
foo -1100 bar"""
    t = create_timesheet(contents)
    entries = t.entries.filter(regroup=True)[datetime.date(2013, 4, 1)]
    assert len(entries) == 2
    assert entries[0].hours == 4


def test_set_pushed_flag_on_regrouped_entry_sets_flag_on_associated_entries():
    contents = """01.04.2013
foo 2 bar
bar 0900-1000 bar
foo 1 bar"""
    t = create_timesheet(contents)
    entries = t.entries.filter(regroup=True)[datetime.date(2013, 4, 1)]
    for entry in entries:
        entry.pushed = True
    lines = t.entries.to_lines()
    assert lines == ["01.04.2013", "= foo 2 bar", "= bar 0900-1000 bar",
                     "= foo 1 bar"]
