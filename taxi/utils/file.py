import codecs
import datetime
import os
import shlex
import subprocess

from taxi.exceptions import TaxiException


def create_file(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    if not os.path.exists(filepath):
        myfile = codecs.open(filepath, 'w', 'utf-8')
        myfile.close()


def spawn_editor(filepath, editor=None):
    if editor is None:
        editor = 'sensible-editor'

    editor = shlex.split(editor)
    editor.append(filepath)

    try:
        subprocess.call(editor)
    except OSError:
        if 'EDITOR' not in os.environ:
            raise TaxiException("Can't find any suitable editor. Check your"
                                " EDITOR env var.")

        editor = shlex.split(os.environ['EDITOR'])
        editor.append(filepath)
        subprocess.call(editor)


def expand_filename(filename, date=None):
    if date is None:
        date = datetime.date.today()

    return date.strftime(os.path.expanduser(filename))
