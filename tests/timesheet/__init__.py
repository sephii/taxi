# -*- coding: utf-8 -*-
import unittest

from taxi.timesheet import Timesheet
from taxi.timesheet.entry import EntriesCollection


class BaseTimesheetTestCase(unittest.TestCase):
    def _create_timesheet(self, text, add_date_to_bottom=False):
        mappings = {'foo': (123, 456), 'bar': (12, 34)}
        entries = EntriesCollection(text)
        entries.add_date_to_bottom = add_date_to_bottom

        return Timesheet(entries, mappings)
