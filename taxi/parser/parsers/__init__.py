from taxi.parser import ParseError

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

    def parse_line(self):
        raise NotImplementedError()

    def _get_current_line(self):
        return self.lines[self.current_line_number - 1]

    def save(self):
        lines = []

        for line in self.parsed_lines:
            lines.append(line.text)

        self.io.write(lines)
