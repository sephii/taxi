from __future__ import unicode_literals

import click

from ..settings import Settings
from ..timesheet.parser import ParseError
from ..timesheet.utils import get_files
from .base import cli, get_timesheet_collection_for_context


@cli.command(short_help="Open the entries file in your editor.")
@click.option('-f', '--file', 'file_to_edit', type=click.Path(dir_okay=False),
              help="Path to the file to edit.")
@click.argument('previous_file', default=0, type=click.IntRange(min=0))
@click.pass_context
def edit(ctx, file_to_edit, previous_file):
    """
    Usage: edit

    Opens your zebra file in your favourite editor.

    The PREVIOUS_FILE argument can be used to specify which nth previous file
    to edit. A value of 1 will edit the previous file, 2 will edit the
    second-previous file, etc.

    If the --file option is used, it will take precedence on the PREVIOUS_FILE
    argument.

    """
    timesheet_collection = None
    forced_file = bool(file_to_edit) or previous_file != 0

    # If the file was not specified and if it's the current file, autofill it
    if not forced_file:
        try:
            timesheet_collection = get_timesheet_collection_for_context(ctx)
        except ParseError:
            pass
        else:
            t = timesheet_collection.timesheets[0]

            if (ctx.obj['settings'].get('auto_add') !=
                    Settings.AUTO_ADD_OPTIONS['NO']):
                auto_fill_days = ctx.obj['settings'].get_auto_fill_days()
                if auto_fill_days:
                    t.prefill(auto_fill_days, limit=None)

                t.file.write(t.entries)

    # Get the path to the file we should open in the editor
    if not file_to_edit:
        timesheet_files = get_files(ctx.obj['settings'].get('file'),
                                    previous_file)
        file_to_edit = list(timesheet_files)[previous_file]

    editor = ctx.obj['settings'].get('editor', default_value='')
    edit_kwargs = {
        'filename': file_to_edit,
        'extension': '.tks'
    }
    if editor:
        edit_kwargs['editor'] = editor

    click.edit(**edit_kwargs)

    try:
        # Show the status only for the given file if it was specified with the
        # --file option, or for the files specified in the settings otherwise
        timesheet_collection = get_timesheet_collection_for_context(
            ctx, file_to_edit if forced_file else None
        )
    except ParseError as e:
        ctx.obj['view'].err(e)
    else:
        ctx.obj['view'].show_status(
            timesheet_collection.get_entries(regroup=True),
            ctx.obj['settings'].get_close_matches
        )
