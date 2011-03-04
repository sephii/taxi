import re
import string
import datetime

from entry import Entry
from settings import Settings

class ParseError(Exception):
    pass

class Parser:
    def process_line(self, line, line_number):
        pass

    def parse(self):
        file = open(self.file, 'r')
        line_number = 0

        for line in file:
            line_number += 1
            self.process_line(line, line_number)

        file.close()

    def __init__(self, file):
        self.file = file
        self.entries = {}

class TaxiParser(Parser):
    def process_date(self, date_matches):
        self.date = datetime.date(int(date_matches.group(3)), int(date_matches.group(2)), int(date_matches.group(1)))

    def process_line(self, line, line_number):
        line = line.strip()

        if len(line) == 0 or line[0] == '#':
            return

        date_matches = re.match('(\d{1,2})\D(\d{1,2})\D(\d{4})', line)

        if date_matches is not None:
            self.process_date(date_matches)
        else:
            self.process_entry(line, line_number)

    def process_entry(self, line, line_number):
        splitted_line = string.split(s = line, maxsplit = 2)

        if len(splitted_line) == 0:
            return
        elif len(splitted_line) != 3:
            raise ParseError('Line #%s is not correctly formatted' % line_number)

        time = re.match('(\d{2}):(\d{2})-(\d{2}):(\d{2})', splitted_line[1])

        if time is not None:
            time_start = datetime.datetime(self.date.year, self.date.month, self.date.day, int(time.group(1)), int(time.group(2)))
            time_end = datetime.datetime(self.date.year, self.date.month, self.date.day, int(time.group(3)), int(time.group(4)))

            total_time = time_end - time_start
            total_hours = total_time.seconds / 3600.0
        else:
            total_hours = float(splitted_line[1])

        if not self.date in self.entries:
            self.entries[self.date] = []

        self.entries[self.date].append(Entry(self.date, splitted_line[0], total_hours, splitted_line[2]))
