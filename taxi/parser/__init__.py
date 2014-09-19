# -*- coding: utf-8 -*-
from taxi.utils import date as date_utils

class ParseError(Exception):
    def __init__(self, message, line_number=None):
        self.message = message
        self.line_number = line_number

    def __str__(self):
        if self.line_number is not None:
            return "Parse error at line %s: %s" % (self.line_number, self.message)
        else:
            return self.message

class TextLine(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.text

    def comment(self):
        if not self.text.startswith('#'):
            self.text = u'# %s' % (self.text)

class EntryLine(TextLine):
    def __init__(self, alias, time, description, text=None):
        self.alias = alias
        self.time = time
        self.description = description

        if text is not None:
            self.text = text
        else:
            self.text = self.generate_text()

    def generate_text(self):
        if isinstance(self.time, tuple):
            start = (self.time[0].strftime('%H:%M') if self.time[0] is not
                     None else '')
            end = (self.time[1].strftime('%H:%M') if self.time[1] is not
                    None else '?')

            time = u'%s-%s' % (start, end)
        else:
            time = self.time

        return u'%s %s %s' % (self.alias, time, self.description)

    def is_ignored(self):
        return self.alias.endswith('?') or self.alias.startswith('?') or self.description == '?'

    def get_alias(self):
        if self.alias.endswith('?'):
            return self.alias[0:-1]

        return self.alias

class DateLine(TextLine):
    def __init__(self, date, text=None, date_format='%d.%m.%Y'):
        self.date = date

        if text is not None:
            self.text = text
        else:
            self.text = date_utils.unicode_strftime(self.date, date_format)

