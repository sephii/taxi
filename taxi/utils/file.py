from __future__ import unicode_literals

import datetime
import os


def expand_filename(filename, date=None):
    if date is None:
        date = datetime.date.today()

    return date.strftime(os.path.expanduser(filename))
