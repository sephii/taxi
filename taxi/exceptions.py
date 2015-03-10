from __future__ import unicode_literals


class TaxiException(Exception):
    pass


class UsageError(TaxiException):
    pass


class CancelException(TaxiException):
    pass


class UndefinedAliasError(TaxiException):
    pass
