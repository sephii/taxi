from ConfigParser import NoOptionError
import calendar
import datetime
import inspect
import re
import subprocess

from taxi.parser import ParseError, TaxiParser
from taxi.projectsdb import projects_db
from taxi.settings import settings
from taxi.utils import file, terminal

def add(options, args):
    """Usage: add search_string

    Searches and prompts for project, activity and alias and adds that as a new
    entry to .tksrc."""

    if len(args) < 2:
        raise Exception(inspect.cleandoc(add.__doc__))

    search = args[1:]
    projects = projects_db.search(search, active_only=True)

    if len(projects) == 0:
        print(u'No project matches your search string \'%s\'' %
              ''.join(search))
        return

    for (key, project) in enumerate(projects):
        print(u'(%d) %-4s %s' % (key, project.id, project.name))

    try:
        number = terminal.select_number(len(projects), 'Choose the project (0-%d), (Ctrl-C) to exit: ' % (len(projects) - 1))
    except KeyboardInterrupt:
        return

    project = projects[number]

    print(project)

    print(u"\nActivities:")
    for (key, activity) in enumerate(project.activities):
        print(u'(%d) %-4s %s' % (key, activity.id, activity.name))

    try:
        number = terminal.select_number(len(project.activities), 'Choose the activity (0-%d), (Ctrl-C) to exit: ' % (len(project.activities) - 1))
    except KeyboardInterrupt:
        return

    retry = True
    while retry:
        try:
            alias = terminal.select_string('Enter the alias for .tksrc (a-z, - and _ allowed), (Ctrl-C) to exit: ', r'^[\w-]+$')
        except KeyboardInterrupt:
            return

        if settings.activity_exists(alias):
            overwrite = terminal.select_string('The selected alias you entered already exists,'\
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

def alias(options, args):
    """Usage: alias [alias]
       alias [project_id/activity_id]
       alias [alias] [project_id/activity_id]

    - The first form will display the mappings whose aliases start with the search
      string you entered
    - The second form will display the mapping you've defined for this
      project/activity tuple
    - The third form will add a new alias in your configuration file

    You can also run this command without any argument to view all your mappings."""

    activity_regexp = r'^(\d{1,4})(?:/(\d{1,4}))?$'
    projects = settings.get_projects()
    search = None

    if len(args) > 3:
        raise Exception(inspect.cleandoc(alias.__doc__))

    # 2 arguments, add a new alias
    if len(args) == 3:
        alias_name = args[1]
        mapping = args[2]

        matches = re.match(activity_regexp, mapping)
        if not matches:
            raise Exception("The mapping must be in the format xxxx/yyyy")

        project_activity = tuple([int(item) if item else None for item in matches.groups()])
        activity = None
        project = projects_db.get(project_activity[0])

        if project:
            activity = project.get_activity(project_activity[1])


        if project is None or activity is None:
            raise Exception("The project/activity tuple was not found in the"
                            " project database. Check your input or update"
                            " your projects database")

        if settings.activity_exists(alias_name):
            (project_id, activity_id) = settings.get_projects()[alias_name]
            project = projects_db.get(project_id)

            if activity_id is not None:
                mapping_name = u'%s/%s' % (project_id, activity_id)
            else:
                mapping_name = str(project_id)

            confirm = terminal.select_string(u"The alias `%s` is already"
                      " mapped to `%s`.\nDo you want to overwrite it [y/N]? " %
                      (alias_name, mapping_name), r'^[yn]$', re.I, 'n')

            if confirm != 'y':
                return

        settings.add_activity(alias_name, matches.group(1), matches.group(2))

    # 1 argument, display the alias or the project id/activity id tuple
    if len(args) == 2:
        search = args[1]

        matches = re.match(activity_regexp, search)
        # project_id/activity_id tuple search
        if matches:
            project_activity = tuple([int(item) if item else None for item in matches.groups()])
            for (user_alias, project_activity) in settings.get_projects().iteritems():
                # check if project id matches search string
                if not str(project_activity[0]).startswith(matches.group(1)):
                    continue

                # check if activity id matches search string
                if matches.group(2) is not None and (
                        project_activity[1] is None or
                        not str(project_activity[1]).startswith(matches.group(2))):
                    continue

                terminal.print_mapping(project_activity)

            return

    # No argument, display the mappings
    if len(args) == 1 or search is not None:
        for (user_alias, project_activity) in settings.get_projects().iteritems():
            if search and not user_alias.startswith(search):
                continue

            terminal.print_alias(user_alias)

def autofill(options, args):
    """Usage: autofill"""

    auto_add = file.get_auto_add_direction(options.file, options.unparsed_file)

    if auto_add != settings.AUTO_ADD_OPTIONS['NO']:
        auto_fill_days = settings.get_auto_fill_days()
        if auto_fill_days:
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)
            last_date = datetime.date(today.year, today.month, last_day[1])

            file.create_file(options.file)
            file.prefill(options.file, auto_add, auto_fill_days, last_date)

def cat(options, args):
    """
   |\      _,,,---,,_
   /,`.-'`'    -.  ;-;;,_
  |,4-  ) )-,_..;\ (  `'-'
 '---''(_/--'  `-'\_)

  Soft kitty, warm kitty
      Little ball of fur
          Happy kitty, sleepy kitty
              Purr, purr, purr"""

    print(cat.__doc__)

def clean_aliases(options, args):
    """Usage: clean-aliases

    Removes aliases from your config file that point to inactive projects."""

    aliases = settings.get_projects()
    inactive_aliases = []

    for (alias, mapping) in aliases.iteritems():
        project = projects_db.get(mapping[0])

        if (project is None or not project.is_active() or
                (mapping[1] is not None and
                project.get_activity(mapping[1]) is None)):
            inactive_aliases.append((alias, mapping))

    if not inactive_aliases:
        print(u"No inactive aliases found.")
        return

    print(u"The following aliases are mapped to inactive projects:\n")
    for (alias, mapping) in inactive_aliases:
        project = projects_db.get(mapping[0])

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

    confirm = terminal.select_string(u"\nDo you want to clean them [y/N]? ", r'^[yn]$',
                            re.I, 'n')

    if confirm == 'y':
        settings.remove_activities([item[0] for item in inactive_aliases])

def commit(options, args):
    """Usage: commit

    Commits your work to the server."""
    parser = TaxiParser(options.file)
    parser.check_entries_mapping(settings.get_projects().keys())

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

def edit(options, args):
    """Usage: edit

    Opens your zebra file in your favourite editor."""
    # Create the file if it does not exist yet
    file.create_file(options.file)

    try:
        auto_add = file.get_auto_add_direction(options.file, options.unparsed_file)
    except ParseError as e:
        pass
    else:
        if auto_add is not None and auto_add != settings.AUTO_ADD_OPTIONS['NO']:
            auto_fill_days = settings.get_auto_fill_days()
            if auto_fill_days:
                file.prefill(options.file, auto_add, auto_fill_days)

            parser = TaxiParser(options.file)
            parser.auto_add(auto_add)
            parser.update_file()

    # Use the 'editor' config var if it's set, otherwise, fall back to
    # sensible-editor
    try:
        editor = settings.get('default', 'editor').split()
    except NoOptionError:
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

def search(options, args):
    """Usage: search search_string

    Searches for a project by its name. The letter in the first column indicates
    the status of the project: [N]ot started, [A]ctive, [F]inished, [C]ancelled."""

    if len(args) < 2:
        raise Exception(inspect.cleandoc(search.__doc__))

    search = args
    search = search[1:]
    projects = projects_db.search(search)
    for project in projects:
        print(u'%s %-4s %s' % (project.get_short_status(), project.id, project.name))

def show(options, args):
    """Usage: show project_id

    Shows the details of the given project_id (you can find it with the search
    command)."""

    if len(args) < 2:
        raise Exception(inspect.cleandoc(show.__doc__))

    try:
        project = projects_db.get(int(args[1]))
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

def start(options, args):
    """Usage: start project_name

    Use it when you start working on the project project_name. This will add the
    project name and the current time to your entries file. When you're
    finished, use the stop command."""

    if len(args) < 2:
        raise Exception(inspect.cleandoc(start.__doc__))

    project_name = args[1]

    if project_name not in settings.get_projects().keys():
        raise ProjectNotFoundError(project_name, 'Error: the project \'%s\' doesn\'t exist' %\
                project_name)

    file.create_file(options.file)

    parser = TaxiParser(options.file)
    auto_add = file.get_auto_add_direction(options.file, options.unparsed_file)
    parser.add_entry(datetime.date.today(), project_name,\
            (datetime.datetime.now().time(), None), auto_add)
    parser.update_file()

def status(options, args):
    """Usage: status

    Shows the summary of what's going to be committed to the server."""

    total_hours = 0

    parser = TaxiParser(options.file)
    parser.check_entries_mapping(settings.get_projects().keys())

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

def stop(options, args):
    """Usage: stop [description]

    Use it when you stop working on the current task. You can add a description
    to what you've done."""

    if len(args) == 2:
        description = args[1]
    else:
        description = None

    parser = TaxiParser(options.file)
    parser.continue_entry(datetime.date.today(), \
            datetime.datetime.now().time(), description)
    parser.update_file()

def update(options, args):
    """Usage: update

    Synchronizes your project database with the server."""

    projects_db.update(
            settings.get('default', 'site'),
            settings.get('default', 'username'),
            settings.get('default', 'password')
    )
