from __future__ import unicode_literals

import datetime

import six

from . import Timesheet, TimesheetCollection, TimesheetFile
from .entry import EntriesCollection
from .parser import ParseError
from ..settings import Settings
from ..utils import file as file_utils
from ..utils.structures import OrderedSet


def get_timesheet_collection(unparsed_file, nb_previous_files, date_format,
                             auto_add):
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
                    timesheet_contents,
                    date_format
                ),
                timesheet_file
            )
        except ParseError as e:
            e.file = file_path
            raise

        # Force new entries direction if necessary
        if (auto_add in [Settings.AUTO_ADD_OPTIONS['TOP'],
                         Settings.AUTO_ADD_OPTIONS['BOTTOM']]):
            t.entries.add_date_to_bottom = (
                auto_add == Settings.AUTO_ADD_OPTIONS['BOTTOM']
            )

        timesheet_collection.timesheets.append(t)

    # Fix `add_date_to_bottom` attribute of timesheet entries based on
    # previous timesheets. When a new timesheet is started it won't have
    # any direction defined, so we take the one from the previous
    # timesheet, if any
    previous_timesheet = None
    for timesheet in reversed(timesheet_collection.timesheets):
        if (timesheet.entries.add_date_to_bottom is None and
                previous_timesheet and
                previous_timesheet.entries.add_date_to_bottom is not None):
            timesheet.entries.add_date_to_bottom = (
                previous_timesheet.entries.add_date_to_bottom
            )
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
