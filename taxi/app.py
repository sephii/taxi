#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import inspect
import locale
from optparse import OptionParser
import os
import sys

from taxi import __version__, commands
from taxi.ui.tty import TtyUi
from taxi.exceptions import ProjectNotFoundError
from taxi.projectsdb import ProjectsDb
from taxi.settings import Settings

class AppContainer(object):
    pass

class Taxi(object):
    def run(self):
        usage = """Usage: %prog [options] command

        Available commands:
          add    \t\tsearches, prompts for project, activity and alias, adds to .tksrc
          autofill \t\tautofills the current timesheet with all the days of the month
          clean-aliases\tremoves aliases that point to inactive projects
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

        # actions = [
        #         (['stat', 'status'], commands.status),
        #         (['ci', 'commit'], commands.commit),
        #         (['up', 'update'], commands.update),
        #         (['search'], commands.search),
        #         (['show'], commands.show),
        #         (['start'], commands.start),
        #         (['stop'], commands.stop),
        #         (['edit'], commands.edit),
        #         (['add'], commands.add),
        #         (['autofill'], commands.autofill),
        #         (['clean-aliases'], commands.clean_aliases),
        #         (['alias'], commands.alias),
        #         (['cat', 'kitty', 'ohai'], commands.cat),
        # ]

        actions = {
            'add': commands.AddCommand,
            'alias': commands.AliasCommand,
            'autofill': commands.AutofillCommand,
            'kitty': commands.KittyCommand,
            'ohai': commands.KittyCommand,
            'clean-aliases': commands.CleanAliasesCommand,
            'commit': commands.CommitCommand,
            'edit': commands.EditCommand,
            'search': commands.SearchCommand,
            'show': commands.ShowCommand,
            'start': commands.StartCommand,
        }

        settings = Settings()
        settings.load(options.config)
        if not os.path.exists(settings.TAXI_PATH):
            os.mkdir(settings.TAXI_PATH)

        if options.file is None:
            try:
                options.file = settings.get('default', 'file')
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
                    splitted_date = options.date.split('-', 1)

                    options.date = (
                            datetime.datetime.strptime(splitted_date[0],
                                                       date_format).date(),
                            datetime.datetime.strptime(splitted_date[1],
                                                       date_format).date()
                            )
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

        try:
            #call_action(actions, options, args)
            action = actions[args[0]](ac)
            action.setup()
            action.validate()
            action.run()
        except ProjectNotFoundError as e:
            if options.verbose:
                raise

            print(e.description)
            print(suggest_project_names(e.project_name))
        except Exception as e:
            if options.verbose:
                raise

            print(e)


def term_unicode(string):
    return unicode(string, sys.stdin.encoding)

def suggest_project_names(project_name):
    close = settings.get_close_matches(project_name)

    if len(close) > 0:
        return 'Did you mean one of the following?\n\n\t%s' % '\n\t'.join(close)

    return ''

def call_action(actions, options, args):
    user_action = args[0]
    display_help = False

    if user_action == 'help':
        user_action = args[1]
        display_help = True
        if user_action == 'help':
            print('YO DAWG you asked for help for the help command. Try to '
                  'search Google in Google instead.')
            return

    for action in actions:
        for action_name in action[0]:
            if action_name == user_action:
                if display_help:
                    print(inspect.cleandoc(action[1].__doc__))
                else:
                    action[1](options=options, args=args)

                return

    raise Exception('Error: action not found')

def main():

    # usage = inspect.cleandoc(main.__doc__)
    # locale.setlocale(locale.LC_ALL, '')
    app = Taxi()
    app.run()


if __name__ == '__main__':
    main()
