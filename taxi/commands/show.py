import click

from taxi.aliases import aliases_database

from ..projects import Project
from .base import cli


@cli.command(short_help="Resolve any object passed to it (aliases, projects, "
                        "etc).")
@click.argument('search', nargs=1)
@click.pass_context
def show(ctx, search):
    """
    Resolves any object passed to it (aliases, projects, etc).

    This will resolve the following:

    \b
        - Aliases (my_alias)
        - Mappings (123/456)
        - Project ids (123)
    """
    matches = {'aliases': [], 'mappings': [], 'projects': []}
    projects_db = ctx.obj['projects_db']

    matches = get_alias_matches(search, matches)
    matches = get_mapping_matches(search, matches, projects_db)
    matches = get_project_matches(search, matches, projects_db)

    ctx.obj['view'].show_command_results(search, matches, projects_db)


def get_alias_matches(search, matches):
    if search in aliases_database:
        matches['aliases'].append(aliases_database[search])

    return matches


def get_mapping_matches(search, matches, projects_db):
    if '/' not in search:
        return matches

    try:
        mapping = Project.str_to_tuple(search)
    except ValueError:
        return matches

    alias_mappings = aliases_database.filter_from_mapping(mapping)
    for alias, alias_mapping in alias_mappings.items():
        matches['mappings'].append((alias_mapping, alias))

    project = projects_db.get(mapping[0])
    project_activity = None

    for activity in project.activities:
        if activity.id == mapping[1]:
            project_activity = activity

    if project and project_activity:
        matches['projects'].append((project, project_activity))

    return matches


def get_project_matches(search, matches, projects_db):
    project = projects_db.get(search)
    if project:
        matches['projects'].append((project, None))

    return matches
