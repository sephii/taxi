import os
import subprocess

def create_file(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    if not os.path.exists(filepath):
        myfile = open(filepath, 'w')
        myfile.close()

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
