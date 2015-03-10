from __future__ import unicode_literals

import datetime

from taxi.timesheet.entry import EntriesCollection, TimesheetEntry


def test_entries_collection_from_string():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0900-1000 Fix coffee machine\ntaxi 2 Work a bit"
    )

    assert len(entries_collection) == 1
    assert len(entries_collection[datetime.date(2014, 1, 20)]) == 2


def test_add_entry_to_entries_collection():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_collection[datetime.date(2014, 1, 20)].append(
        TimesheetEntry('taxi', 4, 'Work a bit')
    )

    assert len(entries_collection[datetime.date(2014, 1, 20)]) == 2


def test_edit_entry_description():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_collection[datetime.date(2014, 1, 20)][0].description = "Fix printer"

    assert entries_collection.lines[-1].text == u"_internal 0800-0900 Fix printer"

def test_edit_entry_duration():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_collection[datetime.date(2014, 1, 20)][0].duration = 5

    assert entries_collection.lines[-1].text == u"_internal 5         Fix coffee machine"

def test_edit_entry_alias():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_collection[datetime.date(2014, 1, 20)][0].alias = 'taxi'

    assert entries_collection.lines[-1].text == u"taxi      0800-0900 Fix coffee machine"


def test_edit_entry_commented():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_collection[datetime.date(2014, 1, 20)][0].commented = True

    assert entries_collection.lines[-1].text == u"# _internal 0800-0900 Fix coffee machine"


def test_edit_entry_ignored():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_collection[datetime.date(2014, 1, 20)][0].ignored = True

    assert entries_collection.lines[-1].text == u"_internal? 0800-0900 Fix coffee machine"


def test_remove_entry_removes_line():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine\ntaxi 2 Work a bit"
    )
    entries_date = datetime.date(2014, 1, 20)
    del entries_collection[entries_date][1]

    assert len(entries_collection[entries_date]) == 1
    assert entries_collection.lines[-1].text == u"_internal 0800-0900 Fix coffee machine"


def test_remove_last_entry_removes_date():
    entries_collection = EntriesCollection(
        "20.01.2014\n_internal 0800-0900 Fix coffee machine"
    )
    entries_date = datetime.date(2014, 1, 20)
    del entries_collection[entries_date][0]

    assert len(entries_collection.lines) == 0


def test_remove_date_removes_lines():
    entries_collection = EntriesCollection("""20.01.2014
_internal 0800-0900 Fix coffee machine
taxi 2 Work a bit
21.01.2014
_internal 0800-0900 Fix printer""")

    entries_date = datetime.date(2014, 1, 20)
    del entries_collection[entries_date]

    assert len(entries_collection.lines) == 2
    assert entries_collection.lines[0].text == "21.01.2014"

def test_insert_to_bottom():
    entries_collection = EntriesCollection("""20.01.2014
_internal 0800-0900 Fix coffee machine""")
    entries_collection.add_date_to_bottom = True

    entries_date = datetime.date(2014, 1, 21)
    entries_collection[entries_date].append(
        TimesheetEntry('taxi', 4, 'Work a bit')
    )

    assert entries_collection.lines[-3].text == "21.01.2014"
    assert entries_collection.lines[-2].text == ""
    assert entries_collection.lines[-1].text == "taxi 4 Work a bit"


def test_insert_to_top():
    entries_collection = EntriesCollection("""20.01.2014
_internal 0800-0900 Fix coffee machine""")
    entries_collection.add_date_to_bottom = False

    entries_date = datetime.date(2014, 1, 21)
    entries_collection[entries_date].append(
        TimesheetEntry('taxi', 4, 'Work a bit')
    )

    assert entries_collection.lines[0].text == "21.01.2014"
    assert entries_collection.lines[1].text == ""
    assert entries_collection.lines[2].text == "taxi 4 Work a bit"
