import click


class TaxiException(click.ClickException):
    pass


class CancelException(TaxiException):
    pass


class ParseError(TaxiException):
    def __init__(self, message, line=None, line_number=None):
        self.line = line
        self.message = message
        self.line_number = line_number
        self.file = None

    def __str__(self):
        if self.line_number is not None and self.file:
            msg = "Parse error in {file} at line {line}: {msg}.".format(
                file=self.file,
                line=self.line_number,
                msg=self.message
            )
        elif self.line_number is not None:
            msg = "Parse error at line {line}: {msg}.".format(
                line=self.line_number,
                msg=self.message
            )
        else:
            msg = self.message

        if self.line:
            msg += " The line causing the error was:\n\n%s" % self.line

        return msg


class NoActivityInProgressError(TaxiException):
    pass


class StopInThePastError(TaxiException):
    pass


class EntriesCollectionValidationError(TaxiException):
    pass
