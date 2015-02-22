from __future__ import unicode_literals

import datetime
import os

import click
import six


class ExpandedPath(click.Path):
    def convert(self, value, *args, **kwargs):
        value = os.path.expanduser(value)
        return super(ExpandedPath, self).convert(value, *args, **kwargs)


class DateRange(click.ParamType):
    """
    Parse dates and return them as ``datetime.date`` objects. Dates can either
    be fixed (eg. 20.01.2014) or ranged (eg. 20.01.2014-22.01.2014). In ranged
    notation, either the start or end date can be left empty (eg. -22.01.2014).

    Dates can also be one of the special values ``yesterday`` and ``today``.
    """
    name = 'date'
    date_format = '%d.%m.%Y'

    def convert(self, value, param, ctx):
        try:
            if '-' in value:
                split_date = value.split('-', 1)

                date_range = (self.to_date(split_date[0]),
                              self.to_date(split_date[1]))

                if all(date_range) and date_range[0] > date_range[1]:
                    raise ValueError("End date should be greater than start "
                                     "date")
            else:
                return self.to_date(value)
        except ValueError as e:
            self.fail(six.text_type(e), param, ctx)

    def to_date(self, date_str):
        relative_values = {
            'yesterday': datetime.timedelta(days=1),
            'today': datetime.timedelta(days=0),
        }

        if not date_str:
            return None

        if date_str in relative_values:
            return datetime.date.today() - relative_values[date_str]

        return datetime.datetime.strptime(date_str, self.date_format).date()


class Hostname(click.ParamType):
    name = 'hostname'

    def convert(self, value, param, ctx):
        if '://' in value:
            value = value[value.find('://') + 3:]

        return value
