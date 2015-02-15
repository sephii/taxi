# -*- coding: utf-8 -*-
import unittest

from taxi.timesheet import Timesheet
from taxi.timesheet.entry import EntriesCollection
from taxi.alias import alias_database, Mapping


class BaseTimesheetTestCase(unittest.TestCase):
    def _create_timesheet(self, text, add_date_to_bottom=False):
        alias_database.update({
            'foo': Mapping(mapping=(123, 456), backend='dummy'),
            'bar': Mapping(mapping=(12, 34), backend='dummy'),
        })
        entries = EntriesCollection(text)
        entries.add_date_to_bottom = add_date_to_bottom

        return Timesheet(entries)
