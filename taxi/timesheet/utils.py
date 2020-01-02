def is_top_down(lines):
    """
    Return `True` if dates in the given lines go in an ascending order, or `False` if they go in a descending order. If
    no order can be determined, return `None`. The given `lines` must be a list of lines, ie.
    :class:`~taxi.timesheet.lines.TextLine`, :class:`taxi.timesheet.lines.Entry` or
    :class:`~taxi.timesheet.lines.DateLine`.
    """
    date_lines = [
        line for line in lines if hasattr(line, 'is_date_line') and line.is_date_line
    ]

    if len(date_lines) < 2 or date_lines[0].date == date_lines[1].date:
        return None
    else:
        return date_lines[1].date > date_lines[0].date


def trim(lines):
    """
    Remove lines at the start and at the end of the given `lines` that are :class:`~taxi.timesheet.lines.TextLine`
    instances and don't have any text.
    """
    trim_top = None
    trim_bottom = None
    _lines = lines[:]

    for (lineno, line) in enumerate(_lines):
        if hasattr(line, 'is_text_line') and line.is_text_line and not line.text.strip():
            trim_top = lineno
        else:
            break

    for (lineno, line) in enumerate(reversed(_lines)):
        if hasattr(line, 'is_text_line') and line.is_text_line and not line.text.strip():
            trim_bottom = lineno
        else:
            break

    if trim_top is not None:
        _lines = _lines[trim_top + 1:]

    if trim_bottom is not None:
        trim_bottom = len(_lines) - trim_bottom - 1
        _lines = _lines[:trim_bottom]

    return _lines
