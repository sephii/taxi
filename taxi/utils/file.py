import datetime
from ConfigParser import NoOptionError
import os

from taxi.parser import ParseError, TaxiParser
from taxi.settings import settings

def prefill(file, direction, auto_fill_days, limit=None):
    parser = TaxiParser(file)
    entries = parser.get_entries()

    if len(entries) == 0:
        today = datetime.date.today()
        cur_date = datetime.date(today.year, today.month, 1)
    else:
        cur_date = max([date for (date, entries) in entries])
        cur_date += datetime.timedelta(days = 1)

    if limit is None:
        limit = datetime.date.today()

    while cur_date <= limit:
        if cur_date.weekday() in auto_fill_days:
            parser.auto_add(direction, cur_date)

        cur_date = cur_date + datetime.timedelta(days = 1)

    parser.update_file()

def create_file(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    if not os.path.exists(filepath):
        myfile = open(filepath, 'w')
        myfile.close()

def get_auto_add_direction(filepath, unparsed_filepath):
    try:
        auto_add = settings.get('default', 'auto_add')
    except NoOptionError:
        auto_add = settings.AUTO_ADD_OPTIONS['AUTO']

    if auto_add == settings.AUTO_ADD_OPTIONS['AUTO']:
        if os.path.exists(filepath):
            auto_add = TaxiParser(filepath).get_entries_direction()
        else:
            auto_add = None

        if auto_add is not None:
            return auto_add

        # Unable to automatically detect the entries direction, we try to get a
        # previous file to see if we're lucky
        yesterday = datetime.date.today() - datetime.timedelta(days=30)
        oldfile = yesterday.strftime(os.path.expanduser(unparsed_filepath))

        if oldfile != filepath:
            try:
                oldparser = TaxiParser(oldfile)
                auto_add = oldparser.get_entries_direction()
            except ParseError:
                pass

    if auto_add is None:
        auto_add = settings.AUTO_ADD_OPTIONS['TOP']

    return auto_add
