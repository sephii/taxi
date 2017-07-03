from __future__ import unicode_literals

import datetime
import functools
import os
import sys

import click
import pkg_resources
import six
from appdirs import AppDirs
from click._termui_impl import Editor

from .. import __version__
from ..aliases import aliases_database
from ..plugins import plugins_registry
from ..projects import ProjectsDb
from ..settings import Settings
from ..timesheet import TimesheetCollection, TimesheetParser
from ..ui.tty import TtyUi
from .types import Date, ExpandedPath, Hostname

xdg_dirs = AppDirs("taxi", "sephii")

# Disable click 5.0 unicode_literals warnings. See
# http://click.pocoo.org/5/python3/
click.disable_unicode_literals_warning = True


def get_timesheet_collection_for_context(ctx, entries_file=None):
    """
    Return a :class:`~taxi.timesheet.TimesheetCollection` object with the current timesheet(s). Since this depends on
    the settings (to get the entries files path, the number of previous files, etc) this uses the settings object from
    the current command context. If `entries_file` is set, this forces the path of the file to be used.
    """
    if not entries_file:
        entries_file = ctx.obj['settings'].get_entries_file_path(False)

    parser = TimesheetParser(
        date_format=ctx.obj['settings']['date_format'],
        add_date_to_bottom=ctx.obj['settings'].get_add_to_bottom(),
        flags_repr=ctx.obj['settings'].get_flags(),
    )

    return TimesheetCollection.load(entries_file, ctx.obj['settings']['nb_previous_files'], parser)


def populate_aliases(aliases):
    aliases_database.reset()
    aliases_database.update(aliases)


def populate_backends(backends):
    plugins_registry.populate_backends(dict(backends))


def create_config_file(filename):
    """
    Create main configuration file if it doesn't exist.
    """
    import textwrap
    from six.moves.urllib import parse

    if not os.path.exists(filename):
        old_default_config_file = os.path.join(os.path.dirname(filename),
                                               '.tksrc')
        if os.path.exists(old_default_config_file):
            upgrade = click.confirm("\n".join(textwrap.wrap(
                "It looks like you recently updated Taxi. Some "
                "configuration changes are required. You can either let "
                "me upgrade your configuration file or do it "
                "manually.")) + "\n\nProceed with automatic configuration "
                "file upgrade?", default=True
            )

            if upgrade:
                settings = Settings(old_default_config_file)
                settings.convert_to_4()
                with open(filename, 'w') as config_file:
                    settings.config.write(config_file)
                os.remove(old_default_config_file)
                return
            else:
                print("Ok then.")
                sys.exit(0)

        welcome_msg = "Welcome to Taxi!"
        click.secho(welcome_msg, fg='green', bold=True)
        click.secho('=' * len(welcome_msg) + '\n', fg='green', bold=True)

        click.echo(click.wrap_text(
            "It looks like this is the first time you run Taxi. You will need "
            "a configuration file ({}) in order to proceed. Please answer a "
            "few questions to create your configuration file.".format(
                filename
            )
        ) + '\n')

        config = pkg_resources.resource_string('taxi', 'etc/taxirc.sample').decode('utf-8')
        context = {}
        available_backends = plugins_registry.get_available_backends()

        context['backend'] = click.prompt(
            "Backend you want to use (choices are %s)" %
            ', '.join(available_backends),
            type=click.Choice(available_backends)
        )
        context['username'] = click.prompt("Username or token")
        context['password'] = parse.quote(
            click.prompt("Password (leave empty if you're using"
                         " a token)", hide_input=True, default=''),
            safe=''
        )
        # Password can be empty in case of token auth so the ':' separator
        # is not included in the template config, so we add it if the user
        # has set a password
        if context['password']:
            context['password'] = ':' + context['password']

        context['hostname'] = click.prompt(
            "Hostname of the backend (eg. timesheets.example.com)",
            type=Hostname()
        )

        editor = Editor().get_editor()
        context['editor'] = click.prompt(
            "Editor command to edit your timesheets", default=editor
        )

        templated_config = config.format(**context)

        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filename, 'w') as f:
            f.write(templated_config)
    else:
        settings = Settings(filename)
        conversions = settings.needed_conversions

        if conversions:
            for conversion in conversions:
                conversion()

            settings.write_config()


class AliasedCommand(click.Command):
    """
    Command that supports a kwarg ``aliases``.
    """
    def __init__(self, *args, **kwargs):
        self.aliases = set(kwargs.pop('aliases', []))
        super(AliasedCommand, self).__init__(*args, **kwargs)


class AliasedGroup(click.Group):
    """
    Command group that supports both custom aliases and prefix-matching. The
    commands are checked in this order:

        * Exact command name
        * Command aliases
        * Command prefix
    """
    def get_command(self, ctx, cmd_name):
        rv = super(AliasedGroup, self).get_command(ctx, cmd_name)
        # Exact command exists, go with this
        if rv is not None:
            return rv

        # Check in aliases
        for name, command in six.iteritems(self.commands):
            if (isinstance(command, AliasedCommand)
                    and cmd_name in command.aliases):
                return super(AliasedGroup, self).get_command(ctx, name)

        # Check in prefixes
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

        return None


def date_options(func):
    """
    Decorator to add support for `--today/--not-today`, `--from` and `--to` options to the given command. The
    calculated date is then passed as a parameter named `date`.
    """
    @click.option(
        '--until', type=Date(), help="Only show entries until the given date."
    )
    @click.option(
        '--since', type=Date(), help="Only show entries starting at the given date.",
    )
    @click.option(
        '--today/--not-today', default=None, help="Only include today's entries (same as --since=today --until=today)"
        " or ignore today's entries (same as --until=yesterday)"
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        since, until, today = kwargs.pop('since'), kwargs.pop('until'), kwargs.pop('today')

        if today is not None:
            if today:
                date = datetime.date.today()
            else:
                date = (None, datetime.date.today() - datetime.timedelta(days=1))
        elif since is not None or until is not None:
            date = (since, until)
        else:
            date = None

        kwargs['date'] = date

        return func(*args, **kwargs)

    return wrapper


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    click.echo('Taxi %s' % __version__)
    ctx.exit()


def get_config_file():
    config_file_name = 'taxirc'

    config_file = os.path.join(os.path.expanduser('~'), '.' + config_file_name)
    if os.path.isfile(config_file):
        return config_file

    return os.path.join(xdg_dirs.user_config_dir, config_file_name)


def get_data_dir():
    data_dir = os.path.join(os.path.expanduser('~'), '.taxi')
    if os.path.isdir(data_dir):
        return data_dir

    return xdg_dirs.user_data_dir


@click.group(cls=AliasedGroup)
@click.option('--config', '-c', default=get_config_file(),
              type=ExpandedPath(dir_okay=False),
              help="Path to the configuration file to use.")
@click.option('--taxi-dir', default=get_data_dir(),
              type=ExpandedPath(file_okay=False), help="Path to the directory "
              "that will be used for internal files.")
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Print version number and exit.")
@click.pass_context
def cli(ctx, config, taxi_dir):
    create_config_file(config)
    settings = Settings(config)

    if not os.path.exists(taxi_dir):
        os.makedirs(taxi_dir)

    populate_aliases(settings.get_aliases())
    populate_backends(settings.get_backends())

    ctx.obj = {}
    ctx.obj['settings'] = settings
    ctx.obj['view'] = TtyUi()
    ctx.obj['projects_db'] = ProjectsDb(os.path.expanduser(taxi_dir))


# This can't be called from inside a command because Click will already have built its commands list
plugins_registry.register_commands()
