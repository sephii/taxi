# -*- coding: utf-8 -*-
import unittest

from taxi.timesheet import Timesheet
from taxi.timesheet.entry import EntriesCollection


class BaseTimesheetTestCase(unittest.TestCase):
    def _create_timesheet(self, text):
        mappings = {'foo': (123, 456), 'bar': (12, 34)}
        entries = EntriesCollection(text)

        return Timesheet(entries, mappings)
