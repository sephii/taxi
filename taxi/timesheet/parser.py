import datetime
import re

from ..exceptions import ParseError
from ..utils import date as date_utils
from .entry import Entry
from .lines import DateLine, TextLine
from .utils import is_top_down, trim


def create_time_from_text(text):
    """
    Parse a time in the form ``hh:mm`` or ``hhmm`` (or even ``hmm``) and return a :class:`datetime.time` object. If no
    valid time can be extracted from the given string, :exc:`ValueError` will be raised.
    """
    text = text.replace(':', '')

    if not re.match(r'^\d{3,}$', text):
        raise ValueError("Time must be numeric")

    minutes = int(text[-2:])
    hours = int(text[0:2] if len(text) > 3 else text[0])

    return datetime.time(hours, minutes)


class TimesheetParser(object):
    """
    The parser takes care of the textual representation of the different line types (dates and entries).
    """
    # Regular expression to match entry lines. This will capture the following groups: flags, spacing1, alias,
    # spacing2, time, start_time, end_time, duration, spacing3, description. Spacings are captured so that indentation
    # can be preserved when reformatting lines. This regexp needs to be "formatted" using the % notation, setting the
    # `flags_repr` value to the list of accepted flags
    ENTRY_LINE_REGEXP = (
        r"^(?:(?P<flags>[%(flags_repr)s]+?)(?P<spacing1>\s+))?"
        r"(?P<alias>[?\w_-]+)(?P<spacing2>\s+)"
        r"(?P<time>(?:(?P<start_time>(?:\d{1,2}):?(?:\d{1,2}))?-(?P<end_time>(?:(?:\d{1,2}):?(?:\d{1,2}))|\?))|"
        r"(?P<duration>(\d+(?:\.\d+)?)|\.\d+))(?P<spacing3>\s+)"
        r"(?P<description>.+)$"
    )
    # Regular expressions to match date lines
    DATE_LINE_REGEXP = re.compile(r'(\d{1,2})\D(\d{1,2})\D(\d{4}|\d{2})')
    US_DATE_LINE_REGEXP = re.compile(r'(\d{4})\D(\d{1,2})\D(\d{1,2})')

    # Position of the different attributes in an entry line. An entry line is:
    # <0: flags><1: spacing1><2: alias><3: spacing2><4: duration><5: spacing3><6: description>
    ENTRY_ATTRS_POSITION = {
        0: 'flags',
        2: 'alias',
        4: 'duration',
        6: 'description',
    }
    # Methods to call to transform a field to text. Fields that are not in this dict won't be transformed for their
    # representation
    ENTRY_ATTRS_TRANSFORMERS = {
        'flags': 'flags_to_text',
        'duration': 'duration_to_text',
    }
    # Format to use to output entry duration
    ENTRY_DURATION_FORMAT = '%H:%M'
    # Default representation of flags
    ENTRY_FLAGS_REPR = {
        Entry.FLAG_IGNORED: '?',
        Entry.FLAG_PUSHED: '=',
    }
    # Methods to call to transform a line instance to its textual representation. These methods will take a single
    # argument, the instance of the line to be transformed
    ENTRY_TRANSFORMERS = {
        DateLine: 'date_line_to_text',
        TextLine: 'text_line_to_text',
        Entry: 'entry_line_to_text',
    }

    def __init__(self, flags_repr=None, add_date_to_bottom=None, date_format='%d.%m.%Y'):
        """
        If `flags_repr` is set, it must be a :class:`dict` where keys are supported flags from
        :class:`~taxi.timesheet.lines.Entry` and the values are a single characters that are unique among all the
        flags.

        If `add_date_to_bottom` is set, it will define whether new dates should be added to the bottom (`True`) or to
        the top (`False`) of the lines. If it's set to `None`, it means the direction detection will be automatic based
        on the existing lines.

        `date_format` is the output date format when transforming the lines to text. This should be a format supported
        by :py:obj:`datetime.date.strftime`:
        """
        self.flags_repr = flags_repr or self.ENTRY_FLAGS_REPR
        self.add_date_to_bottom = add_date_to_bottom
        self.date_format = date_format
        self.entry_line_regexp = self.ENTRY_LINE_REGEXP % {'flags_repr': re.escape(''.join(self.flags_repr.values()))}

    def flags_to_text(self, flags):
        """
        Return the textual representation of the given flags. See :attr:`ENTRY_FLAGS_REPR` for the list of flags.
        """
        return ''.join([self.flags_repr[flag] for flag in flags])

    def duration_to_text(self, duration):
        """
        Return the textual representation of the given `duration`. The duration can either be a tuple of
        :class:`datetime.time` objects, or a simple number. The returned text will be either a hhmm-hhmm string (if the
        given `duration` is a tuple) or a number.
        """
        if isinstance(duration, tuple):
            start = (duration[0].strftime(self.ENTRY_DURATION_FORMAT)
                     if duration[0] is not None
                     else '')

            end = (duration[1].strftime(self.ENTRY_DURATION_FORMAT)
                   if duration[1] is not None
                   else '?')

            duration = '%s-%s' % (start, end)
        else:
            duration = str(duration)

        return duration

    def to_text(self, line):
        """
        Return the textual representation of the given `line`.
        """
        return getattr(self, self.ENTRY_TRANSFORMERS[line.__class__])(line)

    def date_line_to_text(self, date_line):
        """
        Return the textual representation of the given :class:`~taxi.timesheet.lines.DateLine` instance. The date
        format is set by the `date_format` parameter given when instanciating the parser instance.
        """
        # Changing the date in a dateline is not supported yet, but if it gets implemented someday this will need to be
        # changed
        if date_line._text is not None:
            return date_line._text
        else:
            return date_utils.unicode_strftime(date_line.date, self.date_format)

    def text_line_to_text(self, text_line):
        """
        This... well... transforms text to... text.
        """
        return text_line.text

    def entry_line_to_text(self, entry):
        """
        Return the textual representation of an :class:`~taxi.timesheet.lines.Entry` instance. This method is a bit
        convoluted since we don't want to completely mess up the original formatting of the entry.
        """
        line = []

        # The entry is new, it didn't come from an existing line, so let's just return a simple text representation of
        # it
        if not entry._text:
            flags_text = self.flags_to_text(entry.flags)
            duration_text = self.duration_to_text(entry.duration)

            return ''.join(
                (flags_text, ' ' if flags_text else '', entry.alias, ' ', duration_text, ' ', entry.description)
            )

        for i, text in enumerate(entry._text):
            # If this field is mapped to an attribute, check if it has changed
            # and, if so, regenerate its text. The only fields that are not
            # mapped to attributes are spacing fields
            if i in self.ENTRY_ATTRS_POSITION:
                if self.ENTRY_ATTRS_POSITION[i] in entry._changed_attrs:
                    attr_name = self.ENTRY_ATTRS_POSITION[i]
                    attr_value = getattr(entry, self.ENTRY_ATTRS_POSITION[i])

                    # Some attributes need to be transformed to their textual representation, such as flags or duration
                    if attr_name in self.ENTRY_ATTRS_TRANSFORMERS:
                        attr_value = getattr(self, self.ENTRY_ATTRS_TRANSFORMERS[attr_name])(attr_value)
                else:
                    attr_value = text

                line.append(attr_value)
            else:
                # If the length of the field has changed, do whatever we can to keep the current formatting (ie. number
                # of whitespaces)
                if len(line[i-1]) != len(entry._text[i-1]):
                    text = ' ' * max(1, (len(text) - (len(line[i-1]) - len(entry._text[i-1]))))

                line.append(text)

        return ''.join(line).strip()

    def create_entry_line_from_text(self, text):
        """
        Try to parse the given text line and extract and entry. Return an :class:`~taxi.timesheet.lines.Entry`
        object if parsing is successful, otherwise raise :exc:`~taxi.exceptions.ParseError`.
        """
        split_line = re.match(self.entry_line_regexp, text)

        if not split_line:
            raise ParseError("Line must have an alias, a duration and a description")

        alias = split_line.group('alias')
        start_time = end_time = None

        if split_line.group('start_time') is not None:
            if split_line.group('start_time'):
                try:
                    start_time = create_time_from_text(split_line.group('start_time'))
                except ValueError:
                    raise ParseError("Start time is not a valid time, it must be in format hh:mm or hhmm")
            else:
                start_time = None

        if split_line.group('end_time') is not None:
            if split_line.group('end_time') == '?':
                end_time = None
            else:
                try:
                    end_time = create_time_from_text(split_line.group('end_time'))
                except ValueError:
                    raise ParseError("End time is not a valid time, it must be in format hh:mm or hhmm")

        if split_line.group('duration') is not None:
            duration = float(split_line.group('duration'))
        elif start_time or end_time:
            duration = (start_time, end_time)
        else:
            duration = (None, None)

        description = split_line.group('description')

        # Parse and set line flags
        if split_line.group('flags'):
            try:
                flags = self.extract_flags_from_text(split_line.group('flags'))
            # extract_flags_from_text will raise `KeyError` if one of the flags is not recognized. This should never
            # happen though as the list of accepted flags is bundled in self.entry_line_regexp
            except KeyError as e:
                raise ParseError(*e.args)
        else:
            flags = set()

        # Backwards compatibility with previous notation that allowed to end the alias with a `?` to ignore it
        if alias.endswith('?'):
            flags.add(Entry.FLAG_IGNORED)
            alias = alias[:-1]

        if description == '?':
            flags.add(Entry.FLAG_IGNORED)

        line = (
            split_line.group('flags') or '',
            split_line.group('spacing1') or '',
            split_line.group('alias'),
            split_line.group('spacing2'),
            split_line.group('time'),
            split_line.group('spacing3'),
            split_line.group('description'),
        )

        entry_line = Entry(alias, duration, description, flags=flags, text=line)

        return entry_line

    def create_date_from_text(self, text):
        """
        Parse a text in the form dd/mm/yyyy, dd/mm/yy or yyyy/mm/dd and return a corresponding :class:`datetime.date`
        object. If no date can be extracted from the given text, a :exc:`ValueError` will be raised.
        """
        # Try to match dd/mm/yyyy format
        date_matches = re.match(self.DATE_LINE_REGEXP, text)

        # If no match, try with yyyy/mm/dd format
        if date_matches is None:
            date_matches = re.match(self.US_DATE_LINE_REGEXP, text)

        if date_matches is None:
            raise ValueError("No date could be extracted from the given value")

        # yyyy/mm/dd
        if len(date_matches.group(1)) == 4:
            return datetime.date(int(date_matches.group(1)), int(date_matches.group(2)), int(date_matches.group(3)))

        # dd/mm/yy
        if len(date_matches.group(3)) == 2:
            current_year = datetime.date.today().year
            current_millennium = current_year - (current_year % 1000)
            year = current_millennium + int(date_matches.group(3))
        # dd/mm/yyyy
        else:
            year = int(date_matches.group(3))

        return datetime.date(year, int(date_matches.group(2)), int(date_matches.group(1)))

    def extract_flags_from_text(self, text):
        """
        Extract the flags from the given text and return a :class:`set` of flag values. See
        :class:`~taxi.timesheet.lines.Entry` for a list of existing flags.
        """
        flags = set()
        reversed_flags_repr = {v: k for k, v in self.flags_repr.items()}
        for flag_repr in text:
            if flag_repr not in reversed_flags_repr:
                raise KeyError("Flag '%s' is not recognized" % flag_repr)
            else:
                flags.add(reversed_flags_repr[flag_repr])

        return flags

    def parse_text(self, text):
        """
        Parse the given text and return a list of :class:`~taxi.timesheet.lines.DateLine`,
        :class:`~taxi.timesheet.lines.Entry`, and :class:`~taxi.timesheet.lines.TextLine` objects. If there's an
        error during parsing, a :exc:`taxi.exceptions.ParseError` will be raised.
        """
        text = text.strip()
        lines = text.splitlines()
        parsed_lines = []
        encountered_date = False

        for (lineno, line) in enumerate(lines, 1):
            try:
                parsed_line = self.parse_line(line)

                if isinstance(parsed_line, DateLine):
                    encountered_date = True
                elif isinstance(parsed_line, Entry) and not encountered_date:
                    raise ParseError("Entries must be defined inside a date section")
            except ParseError as e:
                # Update exception with some more information
                e.line_number = lineno
                e.line = line
                raise
            else:
                parsed_lines.append(parsed_line)

        return parsed_lines

    def parse_line(self, text):
        """
        Parse the given `text` and return either a :class:`~taxi.timesheet.lines.DateLine`, an
        :class:`~taxi.timesheet.lines.Entry`, or a :class:`~taxi.timesheet.lines.TextLine`, or raise
        :exc:`taxi.exceptions.ParseError` if the line can't be parser. See the transformation methods
        :meth:`create_date_from_text` and :meth:`create_entry_line_from_text` for details about the format the line is
        expected to have.
        """
        text = text.strip().replace('\t', ' ' * 4)

        # The logic is: if the line starts with a #, consider it's a comment (TextLine), otherwise try to parse it as a
        # date and if this fails, try to parse it as an entry. If this fails too, the line is not valid
        if len(text) == 0 or text.startswith('#'):
            parsed_line = TextLine(text)
        else:
            try:
                date = self.create_date_from_text(text)
            except ValueError:
                parsed_line = self.create_entry_line_from_text(text)
            else:
                parsed_line = DateLine(date, text)

        return parsed_line

    def add_date(self, date, lines):
        """
        Return the given `lines` with the `date` added in the right place (ie. to the beginning or to the end of the
        given lines, depending on the `add_date_to_bottom` property).
        """
        _lines = lines[:]
        _lines = trim(_lines)

        if self.add_date_to_bottom is None:
            add_date_to_bottom = is_top_down(lines)
        else:
            add_date_to_bottom = self.add_date_to_bottom

        if add_date_to_bottom:
            _lines.append(TextLine(''))
            _lines.append(DateLine(date))
        else:
            _lines.insert(0, TextLine(''))
            _lines.insert(0, DateLine(date))

        return trim(_lines)
