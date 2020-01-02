import os

import click

from ..utils.date import time_ago_to_date


class ExpandedPath(click.Path):
    def convert(self, value, *args, **kwargs):
        value = os.path.expanduser(value)
        return super(ExpandedPath, self).convert(value, *args, **kwargs)


class Date(click.ParamType):
    """
    Parse the given date and return it as ``datetime.date`` objects. See :func:`taxi.utils.date.time_ago_to_date` for a
    list of accepted formats.
    """
    name = 'date'

    def convert(self, value, param, ctx):
        try:
            return time_ago_to_date(value)
        except ValueError:
            self.fail("Date format {} is not valid".format(value), param, ctx)


class Hostname(click.ParamType):
    name = 'hostname'

    def convert(self, value, param, ctx):
        if '://' in value:
            value = value[value.find('://') + 3:]

        return value
