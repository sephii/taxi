from taxi.timesheet import Timesheet
from taxi.timesheet.entry import EntriesCollection
from taxi.timesheet.parser import TimesheetParser
from taxi.aliases import aliases_database, Mapping


def create_timesheet(text, add_date_to_bottom=False):
    aliases_database.update({
        'foo': Mapping(mapping=(123, 456), backend='test'),
        'bar': Mapping(mapping=(12, 34), backend='test'),
    })
    parser = TimesheetParser(add_date_to_bottom=add_date_to_bottom)
    entries = EntriesCollection(parser, text)

    return Timesheet(entries)
