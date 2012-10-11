#!/usr/bin/python
# -*- coding: utf-8 -*-
from optparse import OptionParser
import ConfigParser
import sys
import os
import datetime
import difflib
import inspect
import subprocess
import re
import calendar

from parser import TaxiParser, ParseError
from settings import settings
from pusher import Pusher
from projectsdb import ProjectsDb

import locale
import taxi

class ProjectNotFoundError(Exception):
    def __init__(self, project_name, description):
        self.project_name = project_name
        self.description = description

    def __str__(self):
        return repr(self.description)

def term_unicode(string):
    return unicode(string, sys.stdin.encoding)

def alias(options, args):
    """Usage: alias [alias]
       alias [project_id/activity_id]

    - The first form will display the mappings whose aliases start with the search
      string you entered
    - The second form will display the mapping you've defined for this
      project/activity tuple

    You can also run this command without any argument to view all your mappings."""

    activity_regexp = r'^(\d{1,4})/(\d{1,4})$'
    projects = settings.get_projects()
    db = ProjectsDb()
    search = None

    if len(args) > 2:
        raise Exception(inspect.cleandoc(alias.__doc__))

    # 1 argument, display the user_alias or the project id/activity id tuple
    if len(args) == 2:
        user_alias = args[1]

        matches = re.match(activity_regexp, user_alias)
        if not matches:
            search = user_alias
        else:
            # project_id/activity_id tuple
            if matches:
                reversed_projects = settings.get_reversed_projects()
                project_activity = (int(matches.group(1)), int(matches.group(2)))
                project = db.get(project_activity[0])

                if project is None:
                    print(u"Project %s doesn't exist." % (project_activity[0]))
                else:
                    if project_activity in reversed_projects:
                        activity = project.get_activity(project_activity[1])

                        if activity is None:
                            print(u"Activity %s/%s doesn't exist." %
                                  project_activity)
                        else:
                            print(u"%s -> %s (%s, %s)" % (user_alias,
                                  reversed_projects[project_activity], project.name,
                                  project.get_activity(project_activity[1]).name))
                    else:
                        print(u"%s is not mapped to any activity." % user_alias)

    # No argument, display the mappings
    if len(args) == 1 or search is not None:
        for (user_alias, project_activity) in settings.get_projects().iteritems():
            if search and not user_alias.startswith(search):
                continue

            project = db.get(project_activity[0])

            if project is None:
                print(u"%s -> ? (%s/%s)" % (user_alias, project_activity[0],
                      project_activity[1]))
            else:
                if project_activity[1] is None:
                    print(u"%s -> %s (%s)" % (user_alias, project.name,
                          project_activity[0]))
                else:
                    activity = project.get_activity(project_activity[1])

                    print(u"%s -> %s, %s (%s/%s)" % (user_alias, project.name,
                          activity.name if activity is not None else '?',
                          project_activity[0], project_activity[1]))

def clean_aliases(options, args):
    """Usage: clean-aliases

    Removes aliases from your config file that point to inactive projects."""

    aliases = settings.get_projects()
    db = ProjectsDb()
    inactive_aliases = []

    for (alias, mapping) in aliases.iteritems():
        project = db.get(mapping[0])

        if (project is None or not project.is_active() or
                (mapping[1] is not None and
                project.get_activity(mapping[1]) is None)):
            inactive_aliases.append((alias, mapping))

    if not inactive_aliases:
        print(u"No inactive aliases found.")
        return

    print(u"The following aliases are mapped to inactive projects:\n")
    for (alias, mapping) in inactive_aliases:
        project = db.get(mapping[0])

        # The project the alias is mapped to doesn't exist anymore
        if project is None:
            project_name = '?'
            mapping_name = '%s/%s' % mapping
        else:
            # The alias is mapped to a project and an activity (it can also be
            # mapped only to a project)
            if mapping[1] is not None:
                activity = project.get_activity(mapping[1])

                # The activity still exists in the project database
                if activity is not None:
                    project_name = '%s, %s' % (project.name, activity.name)
                    mapping_name = '%s/%s' % mapping
                else:
                    project_name = project.name
                    mapping_name = '%s/%s' % mapping
            else:
                project_name = '%s, ?' % (project.name)
                mapping_name = '%s' % (mapping[0])

        print(u"%s -> %s (%s)" % (alias, project_name, mapping_name))

    confirm = select_string(u"\nDo you want to clean them [y/N]? ", r'^[yn]$',
                            re.I, 'n')

    if confirm == 'y':
        settings.remove_activities([item[0] for item in inactive_aliases])

def start(options, args):
    """Usage: start project_name

    Use it when you start working on the project project_name. This will add the
    project name and the current time to your entries file. When you're
    finished, use the stop command."""

    if len(args) < 2:
        raise Exception(inspect.cleandoc(start.__doc__))

    project_name = args[1]

    if not settings.project_exists(project_name):
        raise ProjectNotFoundError(project_name, 'Error: the project \'%s\' doesn\'t exist' %\
                project_name)

    create_file(options.file)

    parser = get_parser(options.file)
    auto_add = get_auto_add_direction(options.file, options.unparsed_file)
    parser.add_entry(datetime.date.today(), project_name,\
            (datetime.datetime.now().time(), None), auto_add)
    parser.update_file()

def stop(options, args):
    """Usage: stop [description]

    Use it when you stop working on the current task. You can add a description
    to what you've done."""

    if len(args) == 2:
        description = args[1]
    else:
        description = None

    parser = get_parser(options.file)
    parser.continue_entry(datetime.date.today(), \
            datetime.datetime.now().time(), description)
    parser.update_file()

def update(options, args):
    """Usage: update

    Synchronizes your project database with the server."""

    db = ProjectsDb()

    db.update(
            settings.get('default', 'site'),
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

def select_number(max, description, min=0):
    while True:
        char = raw_input('\n%s' % description)
        try:
            number = int(char)
            if min <= number <= max:
                return number
            else:
                print(u'Number out of range, try again')
        except ValueError:
            print(u'Please enter a number')

def select_string(description, format=None, regexp_flags=0, default=None):
    while True:
        char = raw_input(description)
        if char == '' and default is not None:
            return default

        if format is not None and re.match(format, char, regexp_flags):
            return char
        else:
            print(u'Invalid input, please try again')

def add(options, args):
    """Usage: add search_string

    Searches and prompts for project, activity and alias and adds that as a new
    entry to .tksrc."""

    db = ProjectsDb()

    if len(args) < 2:
        raise Exception(inspect.cleandoc(add.__doc__))

    search = args[1:]
    projects = db.search(search, active_only=True)

    if len(projects) == 0:
        print(u'No project matches your search string \'%s\'' %
              ''.join(search))
        return

    for (key, project) in enumerate(projects):
        print(u'(%d) %-4s %s' % (key, project.id, project.name))

    try:
        number = select_number(len(projects), 'Choose the project (0-%d), (Ctrl-C) to exit: ' % (len(projects) - 1))
    except KeyboardInterrupt:
        return

    project = projects[number]

    print(project)

    print(u"\nActivities:")
    for (key, activity) in enumerate(project.activities):
        print(u'(%d) %-4s %s' % (key, activity.id, activity.name))

    try:
        number = select_number(len(project.activities), 'Choose the activity (0-%d), (Ctrl-C) to exit: ' % (len(project.activities) - 1))
    except KeyboardInterrupt:
        return

    retry = True
    while retry:
        try:
            alias = select_string('Enter the alias for .tksrc (a-z, - and _ allowed), (Ctrl-C) to exit: ', r'^[\w-]+$')
        except KeyboardInterrupt:
            return

        if settings.activity_exists(alias):
            overwrite = select_string('The selected alias you entered already exists,'\
                ' overwrite? [y/n/R(etry)]: ', r'^[ynr]$', re.I, 'r')

            if overwrite == 'n':
                return
            if overwrite == 'y':
                retry = False
        else:
            retry = False

    activity = project.activities[number]
    settings.add_activity(alias, project.id, activity.id)

    print(u'\nThe following entry has been added to your .tksrc: %s = %s/%s' %
          (alias, project.id, activity.id))

def search(options, args):
    """Usage: search search_string

    Searches for a project by its name. The letter in the first column indicates
    the status of the project: [N]ot started, [A]ctive, [F]inished, [C]ancelled."""

    db = ProjectsDb()

    if len(args) < 2:
        raise Exception(inspect.cleandoc(search.__doc__))

    search = args
    search = search[1:]
    projects = db.search(search)
    for project in projects:
        print(u'%s %-4s %s' % (project.get_short_status(), project.id, project.name))

def autofill(options, args):
    """Usage: autofill"""

    auto_add = get_auto_add_direction(options.file, options.unparsed_file)

    if auto_add != settings.AUTO_ADD_OPTIONS['NO']:
        auto_fill_days = settings.get_auto_fill_days()
        if auto_fill_days:
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)
            last_date = datetime.date(today.year, today.month, last_day[1])

            create_file(options.file)
            _prefill(options.file, auto_add, auto_fill_days, last_date)

def show(options, args):
    """Usage: show project_id

    Shows the details of the given project_id (you can find it with the search
    command)."""

    db = ProjectsDb()

    if len(args) < 2:
        raise Exception(inspect.cleandoc(show.__doc__))

    try:
        project = db.get(int(args[1]))
    except IOError:
        print(u'Error: the projects database file doesn\'t exist. Please run '
              ' `taxi update` to create it')
    except ValueError:
        print(u'Error: the project id must be a number')
    else:
        if project is None:
            print(u"Error: the project doesn't exist")
            return

        print(project)

        if project.is_active():
            print(u"\nActivities:")
            projects_mapping = settings.get_reversed_projects()

            for activity in project.activities:
                if (project.id, activity.id) in projects_mapping:
                    print(u'%-4s %s (mapped to %s)' %
                          (activity.id, activity.name,
                          projects_mapping[(project.id, activity.id)]))
                else:
                    print(u'%-4s %s' % (activity.id, activity.name))

def status(options, args):
    """Usage: status

    Shows the summary of what's going to be committed to the server."""

    total_hours = 0

    parser = get_parser(options.file)
    check_entries_file(parser, settings)

    print(u'Staging changes :\n')
    entries_list = sorted(parser.get_entries(date=options.date))

    for date, entries in entries_list:
        if len(entries) == 0:
            continue

        subtotal_hours = 0
        print(u'# %s #' % date.strftime('%A %d %B').capitalize())
        for entry in entries:
            print(entry)
            subtotal_hours += entry.get_duration() or 0

        print(u'%-29s %5.2f' % ('', subtotal_hours))
        print('')

        total_hours += subtotal_hours

    print(u'%-29s %5.2f' % ('Total', total_hours))
    print(u'\nUse `taxi ci` to commit staging changes to the server')

def commit(options, args):
    """Usage: commit

    Commits your work to the server."""
    parser = get_parser(options.file)
    check_entries_file(parser, settings)

    pusher = Pusher(
            settings.get('default', 'site'),
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )

    entries = parser.get_entries(date=options.date)
    today = datetime.date.today()

    # Get the number of days required to go to the previous open day (ie. not on
    # a week-end)
    if today.weekday() == 6:
        days = 2
    elif today.weekday() == 0:
        days = 3
    else:
        days = 1

    yesterday = today - datetime.timedelta(days=days)

    if options.date is None and not options.ignore_date_error:
        for (date, entry) in entries:
            # Don't take ignored entries into account when checking the date
            ignored_only = True
            for e in entry:
                if not e.is_ignored():
                    ignored_only = False
                    break

            if ignored_only:
                continue

            if date not in (today, yesterday) or date.strftime('%w') in [6, 0]:
                raise Exception('Error: you\'re trying to commit for a day that\'s either'\
                ' on a week-end or that\'s not yesterday nor today (%s).\nTo ignore this'\
                ' error, re-run taxi with the option `--ignore-date-error`' %
                date.strftime('%A %d %B'))

    pusher.push(parser.get_entries(date=options.date))

    total_hours = 0
    ignored_hours = 0
    for date, entries in parser.get_entries(date=options.date):
        for entry in entries:
            if entry.pushed:
                total_hours += entry.get_duration()
            elif entry.is_ignored():
                ignored_hours += entry.get_duration()

    print(u'\n%-29s %5.2f' % ('Total', total_hours))

    if ignored_hours > 0:
        print(u'%-29s %5.2f' % ('Total ignored', ignored_hours))

    parser.update_file()

def _prefill(file, direction, auto_fill_days, limit=None):
    parser = get_parser(file)
    entries = parser.get_entries()

    if len(entries) == 0:
        today = datetime.date.today()
        cur_date = datetime.date(today.year, today.month, 1)
    else:
        cur_date = max([date for (date, entries) in entries])
        cur_date += datetime.timedelta(days = 1)

    if limit is None:
        limit = datetime.date.today()

    while cur_date <= limit:
        if cur_date.weekday() in auto_fill_days:
            parser.auto_add(direction, cur_date)

        cur_date = cur_date + datetime.timedelta(days = 1)

    parser.update_file()

def edit(options, args):
    """Usage: edit

    Opens your zebra file in your favourite editor."""
    # Create the file if it does not exist yet
    create_file(options.file)

    try:
        auto_add = get_auto_add_direction(options.file, options.unparsed_file)
    except ParseError as e:
        pass
    else:
        if auto_add is not None and auto_add != settings.AUTO_ADD_OPTIONS['NO']:
            auto_fill_days = settings.get_auto_fill_days()
            if auto_fill_days:
                _prefill(options.file, auto_add, auto_fill_days)

            parser = get_parser(options.file)
            parser.auto_add(auto_add)
            parser.update_file()

    # Use the 'editor' config var if it's set, otherwise, fall back to
    # sensible-editor
    try:
        editor = settings.get('default', 'editor').split()
    except ConfigParser.NoOptionError:
        editor = ['sensible-editor']

    editor.append(options.file)

    try:
        subprocess.call(editor)
    except OSError:
        if 'EDITOR' not in os.environ:
            raise Exception('Can\'t find any suitable editor. Check your EDITOR'\
            ' env var.')

        subprocess.call([os.environ['EDITOR'], options.file])

    status(options, args)

def get_auto_add_direction(filepath, unparsed_filepath):
    try:
        auto_add = settings.get('default', 'auto_add')
    except ConfigParser.NoOptionError:
        auto_add = settings.AUTO_ADD_OPTIONS['AUTO']

    if auto_add == settings.AUTO_ADD_OPTIONS['AUTO']:
        if os.path.exists(filepath):
            auto_add = get_parser(filepath).get_entries_direction()
        else:
            auto_add = None

        if auto_add is not None:
            return auto_add

        # Unable to automatically detect the entries direction, we try to get a
        # previous file to see if we're lucky
        yesterday = datetime.date.today() - datetime.timedelta(days=30)
        oldfile = yesterday.strftime(os.path.expanduser(unparsed_filepath))

        if oldfile != filepath:
            try:
                oldparser = get_parser(oldfile)
                auto_add = oldparser.get_entries_direction()
            except ParseError:
                pass

    if auto_add is None:
        auto_add = settings.AUTO_ADD_OPTIONS['TOP']

    return auto_add

def get_parser(filename):
    p = TaxiParser(filename)
    p.parse()

    return p

def suggest_project_names(project_name):
    close = settings.get_close_matches(project_name)

    if len(close) > 0:
        return 'Did you mean one of the following?\n\n\t%s' % '\n\t'.join(close)

    return ''

def check_entries_file(parser, settings):
    for date, entries in parser.entries.iteritems():
        for entry in entries:
            if not settings.project_exists(entry.project_name):
                error = 'Error: project `%s` is not mapped to any project number'\
                ' in your settings file' % entry.project_name

                raise ProjectNotFoundError(entry.project_name, error)

def create_file(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    if not os.path.exists(filepath):
        myfile = open(filepath, 'w')
        myfile.close()

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
    """Usage: %prog [options] command

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

    usage = inspect.cleandoc(main.__doc__)
    locale.setlocale(locale.LC_ALL, '')

    opt = OptionParser(usage=usage, version='%prog ' + taxi.__version__)
    opt.add_option('-c', '--config', dest='config', help='use CONFIG file instead of ~/.tksrc', default=os.path.join(os.path.expanduser('~'), '.tksrc'))
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

    actions = [
            (['stat', 'status'], status),
            (['ci', 'commit'], commit),
            (['up', 'update'], update),
            (['search'], search),
            (['show'], show),
            (['start'], start),
            (['stop'], stop),
            (['edit'], edit),
            (['add'], add),
            (['autofill'], autofill),
            (['clean-aliases'], clean_aliases),
            (['alias'], alias),
    ]

    if len(args) == 0 or (len(args) == 1 and args[0] == 'help'):
        opt.print_help()
        exit()

    settings.load(options.config)
    if not os.path.exists(settings.TAXI_PATH):
        os.mkdir(settings.TAXI_PATH)

    if options.file is None:
        try:
            options.file = settings.get('default', 'file')
        except ConfigParser.NoOptionError:
            raise Exception("""Error: no file to parse. You must either define \
one in your config file with the 'file' setting, or use the -f option""")

    options.unparsed_file = options.file
    options.file = datetime.date.today().strftime(os.path.expanduser(options.file))

    if options.date is not None:
        date_format = '%d.%m.%Y'

        try:
            if '-' in options.date:
                splitted_date = options.date.split('-', 1)

                options.date = (datetime.datetime.strptime(splitted_date[0],\
                        date_format).date(),
                        datetime.datetime.strptime(splitted_date[1],
                            date_format).date())
            else:
                options.date = datetime.datetime.strptime(options.date,\
                        date_format).date()
        except ValueError:
            opt.print_help()
            exit()

    try:
        call_action(actions, options, args)
    except ProjectNotFoundError as e:
        if options.verbose:
            raise

        print(e.description)
        print(suggest_project_names(e.project_name))
    except Exception as e:
        if options.verbose:
            raise

        print(e)

if __name__ == '__main__':
    main()
