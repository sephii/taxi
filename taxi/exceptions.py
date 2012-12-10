# -*- coding: utf-8 -*-
class UsageError(Exception):
    pass

class CancelException(Exception):
    pass

class NoActivityInProgressError(Exception):
    pass

class UndefinedAliasError(Exception):
    pass

class UnknownDirectionError(Exception):
    pass
