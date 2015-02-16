# -*- coding: utf-8 -*-
import ConfigParser
import datetime
import inspect
import locale
from optparse import OptionParser
import os
from pkg_resources import resource_filename
import sys
import shutil

from . import __version__, commands
from .alias import alias_database
from .backends.registry import backends_registry
from .exceptions import TaxiException, UsageError
from .projects import ProjectsDb
from .settings import Settings
from .utils.file import expand_filename
from .ui.tty import TtyUi


class AppContainer(object):
    pass


class Taxi(object):
    def run(self):
        usage = """Usage: %prog [options] command

Available commands:
  add    \t\tsearches, prompts for project, activity and alias, adds to .tksrc
  alias  \t\tshows your mappings and allows you to create new ones
  autofill \t\tautofills the current timesheet with all the days of the month
  clean-aliases\t\tremoves aliases that point to inactive projects
  commit \t\tcommits the changes to the server
  edit   \t\topens your zebra file in your favourite editor
  help   \t\tprints this help or the one of the given command
  search \t\tsearches for a project
  show   \t\tshows the activities and other details of a project
  start  \t\tstarts the counter on a given activity
  status \t\tshows the status of your entries file
  stop   \t\tstops the counter and record the elapsed time
  update \t\tupdates your project database with the one on the server"""

        opt = OptionParser(usage=usage, version='%prog ' + __version__)
        opt.add_option('-c', '--config', dest='config',
                       help='use CONFIG file instead of ~/.taxirc',
                       default='~/.taxirc')
        opt.add_option('-v', '--verbose', dest='verbose', action='store_true',
                       help='make taxi verbose', default=False)
        opt.add_option('-f', '--file', dest='file', help='parse FILE instead'
                       ' of the one defined in your CONFIG file')
        opt.add_option('-d', '--date', dest='date', help='only process entries'
                       ' for date DATE (eg. 31.01.2011,'
                       ' 31.01.2011-05.02.2011)')
        opt.add_option(
            '--ignore-date-error', dest='ignore_date_error', help="suppresses"
            " the error if you're trying to commit a date that's on a week-end"
            " or on another day than the current day or the day before",
            action='store_true', default=False
        )
        opt.add_option('-y', '--force-yes', dest='force_yes',
                       help='assume "yes"', action='store_true', default=False)
        (options, args) = opt.parse_args()
        args = [term_unicode(arg) for arg in args]

        if len(args) == 0:
            args = ['help']

        command_args = args[1:] if len(args) > 1 else []
        try:
            self.run_command(args[0], options.__dict__, command_args)
        except UsageError as ue:
            opt.print_help()

            if ue.message:
                print("\nError: %s" % ue.message)

    def run_command(self, command, options={}, args=[]):
        actions = {
            'add': commands.AddCommand,
            'alias': commands.AliasCommand,
            'autofill': commands.AutofillCommand,
            'clean-aliases': commands.CleanAliasesCommand,
            'ci': commands.CommitCommand,
            'commit': commands.CommitCommand,
            'edit': commands.EditCommand,
            'help': commands.HelpCommand,
            'kitty': commands.KittyCommand,
            'ohai': commands.KittyCommand,
            'search': commands.SearchCommand,
            'show': commands.ShowCommand,
            'start': commands.StartCommand,
            'stat': commands.StatusCommand,
            'status': commands.StatusCommand,
            'stop': commands.StopCommand,
            'up': commands.UpdateCommand,
            'update': commands.UpdateCommand,
        }

        options = options.copy()
        args = list(args)

        options['config'] = os.path.expanduser(options['config'])

        self.create_config_file(options['config'])

        settings = Settings(options['config'])
        if not os.path.exists(settings.TAXI_PATH):
            os.mkdir(settings.TAXI_PATH)

        if options.get('file', None) is None:
            options['forced_file'] = False
            try:
                options['file'] = settings.get('file')
            except ConfigParser.NoOptionError:
                raise Exception("Error: no file to parse. You must either "
                                "define one in your config file with the "
                                "'file' setting, or use the -f option")
        else:
            options['forced_file'] = True

        options['unparsed_file'] = os.path.expanduser(options['file'])
        options['file'] = expand_filename(options['file'])

        if options.get('date', None) is not None:
            date_format = '%d.%m.%Y'
            try:
                if '-' in options['date']:
                    split_date = options['date'].split('-', 1)

                    options['date'] = (
                        datetime.datetime.strptime(split_date[0],
                                                   date_format).date(),
                        datetime.datetime.strptime(split_date[1],
                                                   date_format).date())
                else:
                    options['date'] = datetime.datetime.strptime(
                        options['date'], date_format
                    ).date()
            except ValueError:
                raise UsageError("Invalid date format (must be dd.mm.yyyy)")
        else:
            options['date'] = None

        if 'projects_db' not in options:
            options['projects_db'] = os.path.join(
                settings.TAXI_PATH, 'projects.db'
            )

        projects_db = ProjectsDb(options['projects_db'])
        self.populate_aliases(settings.get_aliases(),
                              settings.get_local_aliases())
        self.populate_backends(settings.get_backends())

        view = TtyUi(
            options.get('stdout', sys.stdout),
            settings.get('use_colors').lower() in ['1', 'yes', 'true']
        )
        ac = AppContainer()
        ac.settings = settings
        ac.options = options
        ac.projects_db = projects_db
        ac.arguments = args
        ac.view = view
        action = None

        try:
            if command not in actions:
                raise UsageError("Unknown command `%s`" % command)

            if command == 'help':
                ac.commands_mapping = actions

            action = actions[command](ac)
            action.validate()
            action.setup()
        except UsageError as ue:
            if (action is not None and
                    not isinstance(action, commands.HelpCommand)):
                view.msg(inspect.getdoc(action))
            else:
                raise ue
        else:
            try:
                action.run()
            except TaxiException as e:
                view.err(e)

    def create_config_file(self, filename):
        """
        Create main configuration file if it doesn't exist.
        """
        import textwrap

        if not os.path.exists(filename):
            old_default_config_file = os.path.join(os.path.dirname(filename),
                                                   '.tksrc')
            if os.path.exists(old_default_config_file):
                upgrade = raw_input("\n".join(textwrap.wrap(
                    "It looks like you recently updated Taxi. Some "
                    "configuration changes are required. You can either let "
                    "me upgrade your configuration file or do it "
                    "manually.")) + "\n\nProceed with automatic configuration "
                    "file upgrade? [Y/n]: "
                )

                if not upgrade or upgrade.lower() == 'y':
                    settings = Settings(old_default_config_file)
                    settings.convert_to_4()
                    with open(filename, 'w') as config_file:
                        settings.config.write(config_file)
                    os.remove(old_default_config_file)
                    return
                else:
                    print("Aborting.")
                    sys.exit(0)

            response = raw_input(
                "The configuration file %s does not exist yet.\nDo you want to"
                " create it now? [Y/n]: " % filename
            )

            if not response or response.lower() == 'y':
                src_config = resource_filename('taxi', 'etc/taxirc.sample')
                shutil.copy(src_config, filename)
            else:
                print("Aborting.")
                sys.exit(1)

    def populate_aliases(self, aliases, local_aliases):
        alias_database.update(aliases)

        for alias in local_aliases:
            alias_database.local_aliases.add(alias)

    def populate_backends(self, backends):
        backends_registry.populate(dict(backends))


def term_unicode(string):
    return unicode(string, sys.stdin.encoding)


def main():
    locale.setlocale(locale.LC_ALL, '')

    app = Taxi()
    app.run()
