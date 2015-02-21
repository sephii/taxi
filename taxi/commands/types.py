from __future__ import unicode_literals

import datetime
import os

import click


class ExpandedPath(click.Path):
    def convert(self, value, *args, **kwargs):
        value = os.path.expanduser(value)
        return super(ExpandedPath, self).convert(value, *args, **kwargs)


class DateRange(click.ParamType):
    name = 'date'

    def convert(self, value, param, ctx):
        date_format = '%d.%m.%Y'
        try:
            if '-' in value:
                split_date = value.split('-', 1)

                return (
                    datetime.datetime.strptime(split_date[0],
                                               date_format).date(),
                    datetime.datetime.strptime(split_date[1],
                                               date_format).date()
                )
            else:
                return datetime.datetime.strptime(value, date_format).date()
        except ValueError:
            self.fail("Invalid date format (must be dd.mm.yyyy)", param, ctx)


class Hostname(click.ParamType):
    name = 'hostname'

    def convert(self, value, param, ctx):
        if '://' in value:
            value = value[value.find('://') + 3:]

        return value
