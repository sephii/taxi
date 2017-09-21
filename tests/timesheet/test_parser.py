from __future__ import unicode_literals

import datetime

import pytest

from taxi.exceptions import ParseError
from taxi.timesheet import DateLine, Entry, TextLine
from taxi.timesheet.parser import TimesheetParser, create_time_from_text, trim


def test_extract_date_dot_separator():
    assert TimesheetParser().create_date_from_text('1.1.2010') == datetime.date(2010, 1, 1)


def test_extract_date_slash_separator():
    assert TimesheetParser().create_date_from_text('05/08/2012') == datetime.date(2012, 8, 5)


def test_extract_date_short_year():
    assert TimesheetParser().create_date_from_text('05/08/12') == datetime.date(2012, 8, 5)


def test_extract_date_yyyy_mm_dd():
    assert TimesheetParser().create_date_from_text('2013/08/09') == datetime.date(2013, 8, 9)


def test_extract_date_invalid_string():
    with pytest.raises(ValueError):
        assert TimesheetParser().create_date_from_text('foobar')


def test_extract_date_incomplete_date():
    with pytest.raises(ValueError):
        assert TimesheetParser().create_date_from_text('05/08')


def test_extract_date_missing_separator():
    with pytest.raises(ValueError):
        assert TimesheetParser().create_date_from_text('05.082012')


def test_extract_date_missing_all_separators():
    with pytest.raises(ValueError):
        assert TimesheetParser().create_date_from_text('05082012')


def test_extract_date_yyyy_mm_dd_missing_separator():
    with pytest.raises(ValueError):
        assert TimesheetParser().create_date_from_text('2012/0801')


def test_parse_time_valid_big_integer():
    assert create_time_from_text('0900') == datetime.time(9, 0)


def test_parse_time_invalid_string():
    with pytest.raises(ValueError):
        create_time_from_text('foo')


@pytest.mark.parametrize('duration', ['-2500', '-1061'])
def test_parse_time_out_of_range(duration):
    with pytest.raises(ValueError):
        create_time_from_text(duration)


def test_parse_time_separator_without_timespan():
    with pytest.raises(ValueError):
        create_time_from_text('-')


def test_alias_before_date():
    content = """my_alias_1 1 foo bar
11.10.2013
my_alias 2 foo"""

    with pytest.raises(ParseError):
        TimesheetParser().parse_text(content)

    content = """# comment
11.10.2013
my_alias 2 foo"""

    lines = TimesheetParser().parse_text(content)
    assert len(lines) == 3


@pytest.mark.parametrize('date', ['1110.2013', '11102013'])
def test_invalid_date(date):
    with pytest.raises(ParseError):
        TimesheetParser().parse_text(date)


def test_invalid_line():
    content = """10.01.2013
foobar 0900-1000 baz
foo"""
    with pytest.raises(ParseError):
        TimesheetParser().parse_text(content)


def test_parsing():
    contents = """01.01.13

foobar 0900-1000 baz
# comment
foo -1100 bar

2013/09/23
bar 10:00-? ?
? foo 2 foobar"""

    lines = TimesheetParser().parse_text(contents)

    assert len(lines) == 9
    assert isinstance(lines[0], DateLine)
    assert lines[0].date == datetime.date(2013, 1, 1)
    assert isinstance(lines[1], TextLine)
    assert lines[1].text == ''
    assert isinstance(lines[2], Entry)
    assert lines[2].alias == 'foobar'
    assert lines[2].duration == (datetime.time(9, 0), datetime.time(10, 0))
    assert lines[2].description == 'baz'
    assert isinstance(lines[3], TextLine)
    assert lines[3].text == '# comment'
    assert lines[4].alias == 'foo'
    assert lines[4].duration == (None, datetime.time(11, 0))
    assert lines[4].description == 'bar'
    assert isinstance(lines[6], DateLine)
    assert lines[6].date == datetime.date(2013, 9, 23)
    assert isinstance(lines[7], Entry)
    assert lines[7].duration == (datetime.time(10, 0), None)
    assert isinstance(lines[8], Entry)
    assert lines[8].alias == 'foo'
    assert lines[8].ignored


def test_empty():
    assert len(TimesheetParser().parse_text('')) == 0


def test_stripping_empty():
    lines = TimesheetParser().parse_text("""

""")
    assert len(lines) == 0


def test_stripping_not_empty():
    lines = TimesheetParser().parse_text("""

10.01.2013

foobar 0900-1000 baz

""")
    assert len(lines) == 3


def test_detect_formatting_no_alias_padding():
    line = Entry(
        'foobar', 4, 'description',
    )
    assert TimesheetParser().entry_line_to_text(line) == 'foobar 4 description'


def test_detect_formatting_padded_alias():
    line = Entry(
        'foobar', 4, 'description',
        text=('', '', 'foobar', '   ', '4', ' ', 'description')
    )
    assert TimesheetParser().entry_line_to_text(line) == 'foobar   4 description'


def test_detect_formatting_no_time_padding():
    line = Entry(
        'foobar', (datetime.time(15, 0), datetime.time(16, 0)), 'description',
        text=('', '', 'foobar', ' ', '1500-1600', ' ', 'description')
    )
    assert TimesheetParser().entry_line_to_text(line) == 'foobar 1500-1600 description'


def test_detect_formatting_padded_time():
    line = Entry(
        'foobar', (datetime.time(15, 0), datetime.time(16, 0)), 'description',
        text=('', '', 'foobar', ' ', '1500-1600', '   ', 'description')
    )
    assert TimesheetParser().entry_line_to_text(line) == 'foobar 1500-1600   description'


def test_detect_formatting_padded_time_and_alias():
    line = Entry(
        'foobar', (datetime.time(15, 0), datetime.time(16, 0)), 'description',
        text=('', '', 'foobar', '   ', '1500-1600', '   ', 'description')
    )
    line.duration = (datetime.time(14, 0), datetime.time(15, 0))
    assert TimesheetParser().entry_line_to_text(line) == 'foobar   14:00-15:00 description'


def test_parse_error_contains_line_number():
    try:
        TimesheetParser().parse_text("hello world")
    except ParseError as e:
        assert e.line_number == 1


def test_parse_time_valid_timespan():
    t = TimesheetParser().create_entry_line_from_text('foo 0900-1015 Description')
    assert t.duration == (datetime.time(9, 0), datetime.time(10, 15))


def test_parse_time_valid_timespan_with_separators():
    t = TimesheetParser().create_entry_line_from_text('foo 09:00-10:15 Description')
    assert t.duration == (datetime.time(9, 0), datetime.time(10, 15))


def test_parse_time_valid_timespan_without_end():
    t = TimesheetParser().create_entry_line_from_text('foo 09:00-? Description')
    assert t.duration == (datetime.time(9, 0), None)


def test_parse_time_valid_timespan_without_start():
    t = TimesheetParser().create_entry_line_from_text('foo -10:15 Description')
    assert t.duration == (None, datetime.time(10, 15))


def test_inexistent_flag_raises_parse_error():
    with pytest.raises(ParseError):
        TimesheetParser().create_entry_line_from_text('^ foo 09:00-10:15 Description')


def test_entry_with_flag_keeps_flag():
    t = TimesheetParser().create_entry_line_from_text('= foo 09:00-10:15 Description')
    assert Entry.FLAG_PUSHED in t.flags


def test_trim_trims_to_top():
    entries = [
        TextLine(''),
        DateLine(datetime.date(2017, 4, 1)),
    ]
    assert trim(entries) == entries[1:2]


def test_trim_trims_to_bottom():
    entries = [
        DateLine(datetime.date(2017, 4, 1)),
        TextLine(''),
    ]
    assert trim(entries) == entries[:1]


def test_trim_trims_to_top_and_bottom():
    date_line = DateLine(datetime.date(2017, 4, 1))
    empty_line = TextLine('')

    entries = [
        empty_line,
        empty_line,
        empty_line,
        date_line,
        empty_line,
        date_line,
        empty_line,
        empty_line,
    ]
    assert trim(entries) == [date_line, empty_line, date_line]


def test_parse_entry_with_digits_in_description():
    contents = """01.01.13

foobar 0900-1000 Sprint 1 review
"""

    lines = TimesheetParser().parse_text(contents)

    assert lines[2].alias == 'foobar'
    assert lines[2].duration == (datetime.time(9), datetime.time(10))
    assert lines[2].description == 'Sprint 1 review'


def test_parse_entry_with_description_starting_with_digits():
    contents = """01.01.13

foobar 0900-1000 1 hour of review
"""

    lines = TimesheetParser().parse_text(contents)

    assert lines[2].alias == 'foobar'
    assert lines[2].duration == (datetime.time(9), datetime.time(10))
    assert lines[2].description == '1 hour of review'


def test_parse_continuation_entry_with_unknown_end_time():
    contents = """03.07.2017
alias_1       0845-0930 xxx
alias_1       -? xxx
"""
    lines = TimesheetParser().parse_text(contents)

    assert lines[-1].hours == 0
    assert lines[-1].ignored


def test_parse_entry_with_floating_duration_without_leading_part():
    contents = """03.07.2017
alias_1       .5 xxx
"""
    lines = TimesheetParser().parse_text(contents)

    assert lines[-1].hours == 0.5


def test_invalid_end_time_raises_parse_error():
    contents = """03.07.2017
alias_1 0845-0960 xxx
"""

    with pytest.raises(ParseError):
        TimesheetParser().parse_text(contents)
