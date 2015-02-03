# -*- coding: utf-8 -*-
class TaxiException(Exception):
    pass


class UsageError(TaxiException):
    pass


class CancelException(TaxiException):
    pass


class UndefinedAliasError(TaxiException):
    pass
