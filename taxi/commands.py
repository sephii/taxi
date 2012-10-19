from ConfigParser import NoOptionError
import calendar
import datetime
import inspect
import subprocess

from taxi.exceptions import CancelException, ProjectNotFoundError, UsageError
from taxi.models import Project, Timesheet
from taxi.parser import ParseError, TaxiParser
from taxi.pusher import Pusher
from taxi.settings import Settings
from taxi.utils import file, terminal, date as date_utils

class Command(object):
    def setup(self, app_container):
        self.options = app_container.options
        self.arguments = app_container.arguments
        self.view = app_container.view
        self.projects_db = app_container.projects_db
        self.settings = app_container.settings

    def validate(self):
        pass

    def run(self):
        pass

class TestCommand(Command):
    def run(self):
        p = TaxiParser(self.options.file)
        t = Timesheet(p.parsed_file, self.settings)

class AddCommand(Command):
    """
    Usage: add search_string

    Searches and prompts for project, activity and alias and adds that as a new
    entry to .tksrc.
    """

    def validate(self):
        if len(self.arguments) < 1:
            raise UsageError()

    def run(self):
        search = self.arguments
        projects = self.projects_db.search(search, active_only=True)

        if len(projects) == 0:
            view.msg(u"No project matches your search string '%s" %
                     ''.join(search))
            return

        view.projects_list_numbered(projects, True)

        try:
            number = view.select_project(projects)
        except CancelException:
            return

        project = projects[number]
        view.project_with_activities(project, True)

        try:
            number = view.select_activity(project.activities)
        except CancelException:
            return

        retry = True
        while retry:
            try:
                alias = view.select_alias()
            except CancelException:
                return

            if settings.activity_exists(alias):
                mapping = settings.get_projects()[alias]
                overwrite = terminal.overwrite_alias(alias, mapping)

                if overwrite == False:
                    return
                elif ovewrite == True:
                    retry = False
                # User chose "retry"
                else:
                    retry = True
            else:
                retry = False

        activity = project.activities[number]
        self.settings.add_activity(alias, project.id, activity.id)

        view.alias_added(alias, (project.id, activity.id))

class AliasCommand(Command):
    """
    Usage: alias [alias]
       alias [project_id]
       alias [project_id/activity_id]
       alias [alias] [project_id/activity_id]

    - The first form will display the mappings whose aliases start with the
      search string you entered
    - The second form will display the mapping(s) you've defined for this
      project and all of its activities
    - The third form will display the mapping you've defined for this exact
      project/activity tuple
    - The last form will add a new alias in your configuration file

    You can also run this command without any argument to view all your mappings.
    """

    def validate(self):
        if len(self.arguments) > 2:
            raise UsageError()

    def run(self):
        projects = self.settings.get_projects()
        alias = None

        # 2 arguments, add a new alias
        if len(self.arguments) == 2:
            self._add_alias(self.arguments[0], self.arguments[1])
        # 1 argument, display the alias or the project id/activity id tuple
        elif len(self.arguments) == 1:
            alias = self.arguments[0]
            mapping = Project.str_to_tuple(alias)

            if mapping is not None:
                for m in self.settings.search_aliases(mapping):
                    self.view.mapping_detail(m, self.projects_db.get(m[1][0]))

                return

        # No argument, display the mappings
        if alias is not None or len(self.arguments) == 0:
            for m in self.settings.search_mappings(alias):
                self.view.alias_detail(m, self.projects_db.get(m[1][0]))

    def _add_alias(self, alias_name, mapping):
        project_activity = Project.str_to_tuple(mapping)

        if project_activity is None:
            raise UsageError("The mapping must be in the format xxxx/yyyy")

        activity = None
        project = projects_db.get(project_activity[0])

        if project:
            activity = project.get_activity(project_activity[1])

        if project is None or activity is None:
            raise Exception("Error: the project/activity tuple was not found"
                    " in the project database. Check your input or update your"
                    " projects database.")

        if self.settings.activity_exists(alias_name):
            existing_mapping = settings.get_projects()[alias_name]
            confirm = self.view.confirm_alias(alias_name, existing_mapping, False)

            if not confirm:
                return

        settings.add_activity(alias_name, project_activity[0],
                              project_activity[1])

        self.view.alias_added(alias_name, mapping)

class AutofillCommand(Command):
    """
    Usage: autofill
    """
    # TODO add description

    def run(self):
        try:
            direction = self.settings.get('default', 'auto_add')
        except NoOptionError:
            direction = Settings.AUTO_ADD_OPTIONS['AUTO']

        if direction == Settings.AUTO_ADD_OPTIONS['AUTO']:
            direction = file.get_auto_add_direction(self.options.file,
                                                    self.options.unparsed_file)

        if direction is None:
            direction = Settings.AUTO_ADD_OPTIONS['TOP']

        if direction == Settings.AUTO_ADD_OPTIONS['NO']:
            self.view.err(u"The parameter `auto_add` must have a value that "
                          "is different than 'no' for this command to work.")
        else:
            auto_fill_days = self.settings.get_auto_fill_days()

            if auto_fill_days:
                today = datetime.date.today()
                last_day = calendar.monthrange(today.year, today.month)
                last_date = datetime.date(today.year, today.month, last_day[1])

                file.create_file(self.options.file)
                file.prefill(self.options.file, direction, auto_fill_days, last_date)

                self.view.msg(u"Your entries file has been filled.")
            else:
                self.view.err(u"The parameter `auto_fill_days` must be set to "
                              "use this command.")

class KittyCommand(Command):
    """
   |\      _,,,---,,_
   /,`.-'`'    -.  ;-;;,_
  |,4-  ) )-,_..;\ (  `'-'
 '---''(_/--'  `-'\_)

  Soft kitty, warm kitty
      Little ball of fur
          Happy kitty, sleepy kitty
              Purr, purr, purr
    """

    def run(self):
        self.view.msg(self.__doc__)

class CleanAliasesCommand(Command):
    """Usage: clean-aliases

    Removes aliases from your config file that point to inactive projects."""

    def run(self):
        aliases = self.settings.get_projects()
        inactive_aliases = []

        for (alias, mapping) in aliases.iteritems():
            project = self.projects_db.get(mapping[0])

            if (project is None or not project.is_active() or
                    (mapping[1] is not None and
                    project.get_activity(mapping[1]) is None)):
                inactive_aliases.append(((alias, mapping), project))

        if not inactive_aliases:
            self.view.msg(u"No inactive aliases found.")
            return

        confirm = self.view.clean_inactive_aliases(inactive_aliases)

        if confirm:
            self.settings.remove_activities([item[0] for item in inactive_aliases])
            self.view.msg(u"Inactive aliases have been successfully cleaned.")

class CommitCommand(Command):
    """
    Usage: commit

    Commits your work to the server.
    """

    def run(self):
        parser = TaxiParser(self.options.file)
        parser.check_mappings(self.settings.get_projects().keys())

        if self.options.date is None and not self.options.ignore_date_error:
            non_workday_entries = parser.get_non_current_workday_entries()

            if non_workday_entries:
                dates = [d[0] for d in non_workday_entries]
                self.view.non_working_dates_commit_error(dates)
                return

        pusher = Pusher(self.settings.get('default', 'site'),
                        self.settings.get('default', 'username'),
                        self.settings.get('default', 'password'))
        pusher.push(parser.get_entries(self.options.date, exclude_ignored=True))

        total_hours = 0
        ignored_hours = 0
        for (date, entries) in parser.get_entries(date=options.date):
            for entry in entries:
                if entry.pushed:
                    total_hours += entry.get_duration()
                elif entry.is_ignored():
                    ignored_hours += entry.get_duration()

        self.view.pushed_hours_total(total_hours, ignored_hours)
        parser.update_file()

class EditCommand(Command):
    """
    Usage: edit

    Opens your zebra file in your favourite editor.
    """

    def run(self):
        # Create the file if it does not exist yet
        file.create_file(self.options.file)

        try:
            auto_add = file.get_auto_add_direction(self.options.file,
                                                   self.options.unparsed_file)
        except ParseError as e:
            pass
        else:
            if auto_add is not None and auto_add != Settings.AUTO_ADD_OPTIONS['NO']:
                auto_fill_days = self.settings.get_auto_fill_days()
                if auto_fill_days:
                    file.prefill(self.options.file, auto_add, auto_fill_days)

                parser = TaxiParser(self.options.file)
                parser.auto_add(auto_add,
                                date_format=self.settings.get('default',
                                    'date_format'))
                parser.update_file()

        try:
            editor = self.settings.get('default', 'editor')
        except NoOptionError:
            editor = None

        file.spawn_editor(self.options.file, editor)

        parser = TaxiParser(self.options.file)
        entries = parser.get_entries()
        self.view.show_status(entries)

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
