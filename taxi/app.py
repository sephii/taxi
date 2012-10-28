# -*- coding: utf-8 -*-
import datetime
import inspect
from optparse import OptionParser
import os
import sys

from taxi import __version__, commands
from taxi.exceptions import UndefinedAliasError, UsageError
from taxi.projectsdb import ProjectsDb
from taxi.settings import Settings
from taxi.ui.tty import TtyUi

class AppContainer(object):
    pass

class Taxi(object):
    def run(self):
        usage = """Usage: %prog [options] command

Available commands:
  add    \t\tsearches, prompts for project, activity and alias, adds to .tksrc
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
        opt.add_option('-c', '--config', dest='config', help='use CONFIG file '
                'instead of ~/.tksrc', default='~/.tksrc')
        opt.add_option('-v', '--verbose', dest='verbose', action='store_true', help='make taxi verbose', default=False)
        opt.add_option('-f', '--file', dest='file', help='parse FILE instead of the '\
                'one defined in your CONFIG file')
        opt.add_option('-d', '--date', dest='date', help='only process entries for date '\
                'DATE (eg. 31.01.2011, 31.01.2011-05.02.2011)')
        opt.add_option('--ignore-date-error',
                dest='ignore_date_error', help='suppresses the error if'\
                ' you\'re trying to commit a date that\'s on a week-end or on another'\
                ' day than the current day or the day before', action='store_true', default=False)
        (options, args) = opt.parse_args()
        args = [term_unicode(arg) for arg in args]

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

        settings = Settings(options.config)
        if not os.path.exists(settings.TAXI_PATH):
            os.mkdir(settings.TAXI_PATH)

        if options.file is None:
            try:
                options.file = settings.get('file')
            except ConfigParser.NoOptionError:
                raise Exception("Error: no file to parse. You must either "
                                "define one in your config file with the "
                                "'file' setting, or use the -f option")

        options.unparsed_file = os.path.expanduser(options.file)
        options.file = datetime.date.today().strftime(os.path.expanduser(options.file))

        if options.date is not None:
            date_format = '%d.%m.%Y'

            try:
                if '-' in options.date:
                    split_date = options.date.split('-', 1)

                    options.date = (
                            datetime.datetime.strptime(split_date[0],
                                                       date_format).date(),
                            datetime.datetime.strptime(split_date[1],
                                                       date_format).date())
                else:
                    options.date = datetime.datetime.strptime(options.date,
                                                              date_format).date()
            except ValueError:
                opt.print_help()
                exit()

        projects_db = ProjectsDb(os.path.join(settings.TAXI_PATH, 'projects.db'))

        view = TtyUi()
        ac = AppContainer()
        ac.settings = settings
        ac.options = options
        ac.projects_db = projects_db
        ac.arguments = args[1:]
        ac.view = view
        action = None

        try:
            if len(args) == 0 or args[0] not in actions:
                raise UsageError()

            if args[0] == 'help':
                ac.commands_mapping = actions

            action = actions[args[0]](ac)
            action.setup()
            action.validate()
        except UsageError:
            if (action is not None and
                    not isinstance(action, commands.HelpCommand)):
                view.msg(inspect.getdoc(action))
            else:
                view.msg(opt.format_help())
        else:
            try:
                action.run()
            except UndefinedAliasError as e:
                close = settings.get_close_matches(e.message)
                view.suggest_aliases(e.message, close)

def term_unicode(string):
    return unicode(string, sys.stdin.encoding)

def main():
    app = Taxi()
    app.run()
