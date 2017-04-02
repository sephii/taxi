from __future__ import unicode_literals

import datetime

import six

from . import Timesheet, TimesheetCollection, TimesheetFile
from .entry import EntriesCollection
from .parser import ParseError
from ..utils import file as file_utils
from ..utils.structures import OrderedSet


def get_timesheet_collection(unparsed_file, nb_previous_files, parser):
    timesheet_collection = TimesheetCollection()

    timesheet_files = get_files(unparsed_file, nb_previous_files)

    for file_path in timesheet_files:
        timesheet_file = TimesheetFile(file_path)
        try:
            timesheet_contents = timesheet_file.read()
        except IOError:
            timesheet_contents = ''

        try:
            t = Timesheet(
                EntriesCollection(
                    parser,
                    timesheet_contents,
                ),
                timesheet_file
            )
        except ParseError as e:
            e.file = file_path
            raise

        timesheet_collection.timesheets.append(t)

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


def get_files(filename, nb_previous_files, from_date=None):
    date_units = ['m', 'Y']
    smallest_unit = None

    if not from_date:
        from_date = datetime.date.today()

    for date in date_units:
        if '%%%s' % date in filename:
            smallest_unit = date
            break

    if smallest_unit is None:
        return OrderedSet([filename])

    files = OrderedSet()
    file_date = from_date
    for i in six.moves.xrange(0, nb_previous_files + 1):
        files.add(file_utils.expand_date(filename, file_date))

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
