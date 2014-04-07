# -*- coding: utf-8 -*-
import unittest

from taxi.models import Timesheet
from taxi.parser.io import StreamIo
from taxi.parser.parsers.plaintext import PlainTextParser


class BaseTimesheetTestCase(unittest.TestCase):
    def _create_timesheet(self, text):
        mappings = {'foo': (123, 456), 'bar': (12, 34)}
        io = StreamIo(text)
        p = PlainTextParser(io)

        return Timesheet(p, mappings, '%d.%m.%Y')
