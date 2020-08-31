import click

from ..exceptions import EntriesCollectionValidationError, ParseError
from .base import cli, date_options, get_timesheet_collection_for_context


@cli.command(short_help="Show a summary of your entries.")
@click.option('-f', '--file', 'f', type=click.Path(dir_okay=False),
              help="Path to the entries file to use.")
@click.option('--pushed', is_flag=True, help="Include pushed entries.")
@date_options
@click.pass_context
def status(ctx, date, f, pushed):
    """
    Shows the summary of what's going to be committed to the server.
    """
    try:
        timesheet_collection = get_timesheet_collection_for_context(ctx, f)
    except (ParseError, EntriesCollectionValidationError) as e:
        ctx.obj['view'].err(e)
    else:
        ctx.obj['view'].show_status(
            timesheet_collection.entries.filter(
                date, regroup=ctx.obj['settings']['regroup_entries'],
                pushed=False if not pushed else None
            )
        )
