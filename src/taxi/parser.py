import re
import string
import datetime

from models import Entry

class ParseError(Exception):
    pass

class Parser:
    def process_line(self, line, line_number):
        pass

    def parse(self):
        file = open(self.file, 'r')
        line_number = 0

        for line in file:
            self.lines.insert(line_number, {'text': line, 'entry': None})
            self.process_line(line, line_number)
            line_number += 1

        file.close()

    def __init__(self, file):
        self.file = file
        self.entries = {}
        self.lines = []

class TaxiParser(Parser):
    def process_date(self, date_matches):
        if len(date_matches.group(3)) == 2:
            current_year = datetime.date.today().year
            current_millennium = current_year - (current_year % 1000)
            year = current_millennium + int(date_matches.group(3))
        else:
            year = int(date_matches.group(3))

        return datetime.date(year, int(date_matches.group(2)), int(date_matches.group(1)))

    def _match_date(self, line):
        return re.match('(\d{1,2})\D(\d{1,2})\D(\d{4}|\d{2})', line)

    def process_line(self, line, line_number):
        line = line.strip()

        if len(line) == 0 or line[0] == '#':
            return

        date_matches = self._match_date(line)

        if date_matches is not None:
            self.date = self.process_date(date_matches)
        else:
            entry = self.process_entry(line, line_number)

            if not self.date in self.entries:
                self.entries[self.date] = []

            self.entries[self.date].append(entry)
            self.lines[line_number]['entry'] = entry

    def process_entry(self, line, line_number):
        splitted_line = string.split(s = line, maxsplit = 2)

        if len(splitted_line) == 0:
            return
        elif len(splitted_line) != 3:
            raise ParseError('Line #%s is not correctly formatted' % line_number)

        time = re.match(r'(\d{2}):(\d{2})-(?:(?:(\d{2}):(\d{2}))|\?)', splitted_line[1])

        if time is not None:
            time_start = datetime.time(int(time.group(1)), int(time.group(2)))

            if time.group(3) is not None and time.group(4) is not None:
                time_end = datetime.time(int(time.group(3)), int(time.group(4)))
                total_hours = (time_start, time_end)
            else:
                total_hours = (time_start, None)
        else:
            try:
                total_hours = float(splitted_line[1])
            except ValueError:
                raise ParseError('Line #%s is not correctly formatted' % line_number)

        return Entry(self.date, splitted_line[0], total_hours, splitted_line[2])

    def update_file(self):
        file = open(self.file, 'w')

        for line in self.lines:
            text = line['text']

            if line['entry'] is not None and line['entry'].pushed:
                text = '# %s' % text

            file.write(text)

        file.close()

    def get_entries(self, date=None):
        if date is None:
            return self.entries.iteritems()

        if not isinstance(date, tuple):
            date = (date, date)

        entries = [(entrydate, entry) for entrydate, entry in self.entries.iteritems() if \
                entrydate >= date[0] and entrydate <= date[1]]

        return entries

    def add_entry(self, date, project, duration=None):
        if date not in self.entries:
            self.entries[date] = []

        new_entry = Entry(date, project, duration, '?')
        new_text = self.get_line_text(new_entry)

        new_line = {
                'entry': new_entry,
                'text': new_text,
        }
        self.entries[date].append(new_entry)

        current_date = None
        latest_entry = None

        for lineno, line in enumerate(self.lines):
            if line['entry'] is None:
                if latest_entry is not None:
                    break

                datematches = self._match_date(line['text'])

                if datematches is not None:
                    current_date = self.process_date(datematches)
            elif current_date == date:
                latest_entry = lineno

        if latest_entry is not None:
            self.lines.insert(lineno, new_line)
        else:
            new_line['text'] += '\n'
            self.lines.insert(0, {'text': '%s\n' % date.strftime('%d/%m/%Y'),\
                'entry': None})
            self.lines.insert(1, {'text': '\n', 'entry': None})
            self.lines.insert(2, new_line)

    def continue_entry(self, date, project, end, description=None):
        found_entry = None
        for entry in self.entries[date]:
            if entry.get_duration() is None and entry.project_name == project:
                found_entry = entry
                break

        if found_entry is None:
            raise Exception('Error: no activity in progress found')

        for lineno, line in enumerate(self.lines):
            if line['entry'] == found_entry:
                found_entry.duration = (found_entry.duration[0],\
                        datetime.datetime.now().time())
                self.lines[lineno]['text'] = self.get_line_text(found_entry)

    def get_line_text(self, entry):
        if isinstance(entry.duration, tuple):
            if entry.duration[0] is not None:
                txtduration = entry.duration[0].strftime('%H:%M')

                if entry.duration[1] is not None:
                    txtduration += '-%s' % entry.duration[1].strftime('%H:%M')
                else:
                    txtduration += '-?'
            else:
                txtduration = '?'
        else:
            txtduration = entry.duration

        return '%s %s %s\n' % (entry.project_name, txtduration,\
                entry.description or '?')
