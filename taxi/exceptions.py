from __future__ import unicode_literals

import click


class TaxiException(click.ClickException):
    pass


class CancelException(TaxiException):
    pass
