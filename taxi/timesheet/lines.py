class TextLine(object):
    """
    The TextLine is either a blank line or a comment line.
    """
    is_text_line = True

    def __init__(self, text):
        super(TextLine, self).__init__()
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return '<TextLine: "%s">' % str(self.text)


class DateLine(object):
    """
    Represents a date in a timesheet.
    """
    is_date_line = True

    def __init__(self, date, text=None):
        super(DateLine, self).__init__()

        self._text = text
        self.date = date

    def __repr__(self):
        return '<DateLine: "%s">' % (self._text if self._text else self.date)
