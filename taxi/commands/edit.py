from __future__ import unicode_literals

import click

from ..settings import Settings
from ..timesheet.parser import ParseError
from .base import cli, get_timesheet_collection_for_context


@cli.command(short_help="Open the entries file in your editor.")
@click.option('-f', '--file', 'f', type=click.Path(dir_okay=False),
              help="Path to the file to edit.")
@click.pass_context
def edit(ctx, f):
    """
    Usage: edit

    Opens your zebra file in your favourite editor.

    """
    timesheet_collection = None

    try:
        timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    except ParseError:
        pass

    if timesheet_collection:
        t = timesheet_collection.timesheets[0]

        if (ctx.obj['settings'].get('auto_add') !=
                Settings.AUTO_ADD_OPTIONS['NO'] and not f):
            auto_fill_days = ctx.obj['settings'].get_auto_fill_days()
            if auto_fill_days:
                t.prefill(auto_fill_days, limit=None)

            t.file.write(t.entries)

    file_to_edit = f if f else ctx.obj['settings'].get_entries_file_path()
    editor = ctx.obj['settings'].get('editor', default_value='')
    edit_kwargs = {
        'filename': file_to_edit,
        'extension': '.tks'
    }
    if editor:
        edit_kwargs['editor'] = editor

    click.edit(**edit_kwargs)

    try:
        timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    except ParseError as e:
        ctx.obj['view'].err(e)
    else:
        ctx.obj['view'].show_status(
            timesheet_collection.get_entries(regroup=True),
            ctx.obj['settings'].get_close_matches
        )
