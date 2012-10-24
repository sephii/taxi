# -*- coding: utf-8 -*-

class ParseError(Exception):
    pass

class TextLine(object):
    def __init__(self, text):
        self.text = text

    def __str__(self):
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
            if isinstance(self.time, tuple):
                start = (self.time[0].strftime('%H:%M') if self.time[0] is not
                         None else '')
                end = (self.time[1].strftime('%H:%M') if self.time[1] is not
                        None else '?')

                time = '%s-%s' % (start, end)
            else:
                time = self.time

            self.text = '%s %s %s' % (self.alias, time, self.description)

    def is_ignored(self):
        return self.alias.endswith('?')

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
            self.text = self.date.strftime(date_format)

