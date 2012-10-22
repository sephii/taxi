from ConfigParser import NoOptionError
import datetime
import os
import subprocess

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
