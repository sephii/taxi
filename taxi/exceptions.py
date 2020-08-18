import click


class TaxiException(click.ClickException):
    pass


class CancelException(TaxiException):
    pass


class TimesheetError(TaxiException):
    def __init__(self, message, line=None, line_number=None):
        self.line = line
        self.message = message
        self.line_number = line_number
        self.file = None

    def __str__(self):
        parts = [
            "in file {}".format(self.file) if self.file else None,
            "at line {}".format(self.line_number) if self.line_number else None,
        ]

        msg = "Error {parts}:{line}\n\n{message}".format(
            parts=" ".join(part for part in parts if part),
            line="\n\n\t{line}".format(line=self.line) if self.line else "",
            message=self.message
        )

        return msg


class ParseError(TimesheetError):
    pass


class NoActivityInProgressError(TaxiException):
    pass


class StopInThePastError(TaxiException):
    pass


class EntriesCollectionValidationError(TimesheetError):
    pass
