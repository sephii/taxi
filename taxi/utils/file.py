from ConfigParser import NoOptionError
import datetime
import os
import subprocess

from taxi.parser import ParseError, TaxiParser

def prefill(file, direction, auto_fill_days, limit=None, date_format='%d/%m/%Y'):
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
            parser.auto_add(direction, cur_date, date_format=date_format)

        cur_date = cur_date + datetime.timedelta(days = 1)

    parser.update_file()

def create_file(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    if not os.path.exists(filepath):
        myfile = open(filepath, 'w')
        myfile.close()

def get_auto_add_direction(filepath, unparsed_filepath):
    if os.path.exists(filepath):
        auto_add = TaxiParser(filepath).get_entries_direction()
    else:
        auto_add = None

    if auto_add is not None:
        return auto_add

    # Unable to automatically detect the entries direction, we try to get a
    # previous file to see if we're lucky
    prev_month = datetime.date.today() - datetime.timedelta(days=30)
    oldfile = prev_month.strftime(unparsed_filepath)

    if oldfile != filepath:
        try:
            oldparser = TaxiParser(oldfile)
            auto_add = oldparser.get_entries_direction()
        except ParseError:
            pass

    return auto_add

def spawn_editor(filepath, editor=None):
    if editor is None:
        editor = 'sensible-editor'

    editor = editor.split()
    editor.append(filepath)

    try:
        subprocess.call(editor)
    except OSError:
        if 'EDITOR' not in os.environ:
            raise Exception("Can't find any suitable editor. Check your EDITOR "
                            " env var.")

        editor = os.environ['EDITOR'].split()
        editor.append(filepath)
        subprocess.call(editor)
