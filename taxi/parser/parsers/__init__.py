from taxi.parser import ParseError, TextLine

class BaseParser(object):
    def __init__(self, io):
        self.io = io
        self.entries = {}
        self.lines = io.read()
        self.parsed_lines = []

        self.parse()

    def parse(self):
        self.current_line_number = 1

        try:
            for line in self.lines:
                self.parsed_lines.append(self.parse_line())
                self.current_line_number += 1
        except ParseError as e:
            e.line_number = self.current_line_number
            raise

        self.strip_lines()

    def parse_line(self):
        raise NotImplementedError()

    def strip_lines(self):
        start = stop = 0

        for (index, line) in enumerate(self.parsed_lines):
            if not self.is_empty_line(line):
                start = index
                break

        for (index, line) in enumerate(reversed(self.parsed_lines)):
            if not self.is_empty_line(line):
                stop = len(self.parsed_lines) - index
                break

        # Only empty lines
        if start == stop == 0:
            self.parsed_lines = []
            self.lines = []
        else:
            self.parsed_lines = self.parsed_lines[start:stop]
            self.lines = self.lines[start:stop]

    def is_empty_line(self, line):
        return isinstance(line, TextLine) and line.text == ''

    def _get_current_line(self):
        return self.lines[self.current_line_number - 1]

    def save(self):
        lines = []

        for line in self.parsed_lines:
            lines.append(line.text)

        self.io.write(lines)
