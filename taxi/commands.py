# -*- coding: utf-8 -*-
from ConfigParser import NoOptionError
import calendar
import datetime

from taxi import remote
from taxi.exceptions import (
        NoActivityInProgressError,
        CancelException,
        UndefinedAliasError,
        UnknownDirectionError,
        UsageError
)
from taxi.models import Entry, Project, Timesheet
from taxi.parser import ParseError
from taxi.parser.parsers.plaintext import PlainTextParser
from taxi.parser.io import PlainFileIo
from taxi.settings import Settings
from taxi.utils import file, terminal, date as date_utils

class BaseCommand(object):
    def __init__(self, app_container):
        self.options = app_container.options
        self.arguments = app_container.arguments
        self.view = app_container.view
        self.projects_db = app_container.projects_db
        self.settings = app_container.settings

    def setup(self):
        pass

    def validate(self):
        pass

    def run(self):
        pass

class BaseTimesheetCommand(BaseCommand):
    def get_timesheet(self, skip_cache=False):
        timesheet = getattr(self, '_current_timesheet', None)
        if timesheet is not None and not skip_cache:
            return timesheet

        p = PlainTextParser(PlainFileIo(self.options.file))
        t = Timesheet(p, self.settings.get_projects(),
                      self.settings.get('date_format'))
        setattr(self, '_current_timesheet', t)

        return t

    def get_entries_direction(self):
        is_top_down = None

        try:
            t = self.get_timesheet()
        except ParseError:
            pass

        if self.settings.get('auto_add') == Settings.AUTO_ADD_OPTIONS['AUTO']:
            if t is not None:
                try:
                    is_top_down = t.is_top_down()
                except ParseError, UnknownDirectionError:
                    is_top_down = None

            if is_top_down is None:
                # Unable to automatically detect the entries direction, we try to get a
                # previous file to see if we're lucky
                prev_month = datetime.date.today() - datetime.timedelta(days=30)
                oldfile = prev_month.strftime(unparsed_filepath)

                try:
                    p = PlainTextParser(PlainFileIo(oldfile))
                    t2 = Timesheet(p, self.settings.get_projects(),
                                   self.settings.get('date_format'))
                    is_top_down = t2.is_top_down()
                except ParseError, UnknownDirectionError:
                    is_top_down = False
        else:
            is_top_down = (self.settings.get('auto_add') ==
                           Settings.AUTO_ADD_OPTIONS['BOTTOM'])

        return is_top_down

class AddCommand(BaseCommand):
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
        projects = sorted(projects, key=lambda project: project.name)

        if len(projects) == 0:
            view.msg(u"No project matches your search string '%s" %
                     ''.join(search))
            return

        self.view.projects_list(projects, True)

        try:
            number = self.view.select_project(projects)
        except CancelException:
            return

        project = projects[number]
        mappings = self.settings.get_reversed_projects()
        self.view.project_with_activities(project, mappings, numbered_activities=True)

        try:
            number = self.view.select_activity(project.activities)
        except CancelException:
            return

        retry = True
        while retry:
            try:
                alias = self.view.select_alias()
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

        self.view.alias_added(alias, (project.id, activity.id))

class AliasCommand(BaseCommand):
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
    MODE_SHOW_MAPPING = 0
    MODE_ADD_ALIAS = 1
    MODE_LIST_ALIASES = 2

    def validate(self):
        if len(self.arguments) > 2:
            raise UsageError()

    def setup(self):
        if len(self.arguments) == 2:
            self.alias = self.arguments[0]
            self.mapping = self.arguments[1]
            self.mode = self.MODE_ADD_ALIAS
        elif len(self.arguments) == 1:
            self.alias = self.arguments[0]
            self.mode = self.MODE_SHOW_MAPPING
        else:
            self.alias = None
            self.mode = self.MODE_LIST_ALIASES

    def run(self):
        projects = self.settings.get_projects()

        # 2 arguments, add a new alias
        if self.mode == self.MODE_ADD_ALIAS:
            self._add_alias(self.alias, self.mapping)
        # 1 argument, display the alias or the project id/activity id tuple
        elif self.mode == self.MODE_SHOW_MAPPING:
            mapping = Project.str_to_tuple(self.alias)

            if mapping is not None:
                for m in self.settings.search_aliases(mapping):
                    self.view.mapping_detail(m, self.projects_db.get(m[1][0]))
            else:
                self.mode = self.MODE_LIST_ALIASES

        # No argument, display the mappings
        if self.mode == self.MODE_LIST_ALIASES:
            for m in self.settings.search_mappings(self.alias):
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

class AutofillCommand(BaseTimesheetCommand):
    """
    Usage: autofill

    Fills your timesheet up to today, for the defined auto_fill_days.

    """
    def run(self):
        try:
            direction = self.settings.get('auto_add')
        except NoOptionError:
            direction = Settings.AUTO_ADD_OPTIONS['AUTO']

        if direction == Settings.AUTO_ADD_OPTIONS['NO']:
            self.view.err(u"The parameter `auto_add` must have a value that "
                          "is different than 'no' for this command to work.")
            return

        if direction == Settings.AUTO_ADD_OPTIONS['AUTO']:
            try:
                direction = self.get_entries_direction()
            except UnknownDirectionError:
                direction = None

        if direction is None:
            direction = Settings.AUTO_ADD_OPTIONS['TOP']

        auto_fill_days = self.settings.get_auto_fill_days()

        if auto_fill_days:
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)
            last_date = datetime.date(today.year, today.month, last_day[1])
            add_to_bottom = direction == Settings.AUTO_ADD_OPTIONS['BOTTOM']

            file.create_file(self.options.file)
            p = PlainTextParser(PlainFileIo(self.options.file))
            t = Timesheet(p, self.settings.get_projects(),
                          self.settings.get('date_format'))

            t.prefill(auto_fill_days, last_date, add_to_bottom)
            t.save()

            self.view.msg(u"Your entries file has been filled.")
        else:
            self.view.err(u"The parameter `auto_fill_days` must be set to "
                          "use this command.")

class KittyCommand(BaseCommand):
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

class CleanAliasesCommand(BaseCommand):
    """
    Usage: clean-aliases

    Removes aliases from your config file that point to inactive projects.

    """
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

class CommitCommand(BaseTimesheetCommand):
    """
    Usage: commit

    Commits your work to the server.

    """
    def run(self):
        t = self.get_timesheet()

        if self.options.date is None and not self.options.ignore_date_error:
            non_workday_entries = t.get_non_current_workday_entries()

            if non_workday_entries:
                dates = [d[0] for d in non_workday_entries]
                self.view.non_working_dates_commit_error(dates)

                return

        self.view.pushing_entries()
        r = remote.ZebraRemote(self.settings.get('site'),
                               self.settings.get('username'),
                               self.settings.get('password'))
        entries_to_push = t.get_entries(self.options.date, exclude_ignored=True)
        (pushed_entries, failed_entries) = r.send_entries(entries_to_push,
                                                          self._entry_pushed)

        t.comment_entries(pushed_entries)
        t.save()

        ignored_entries = t.get_ignored_entries(self.options.date)
        ignored_entries_list = []
        for (date, entries) in ignored_entries.iteritems():
            ignored_entries_list.extend(entries)

        self.view.pushed_entries_summary(pushed_entries, failed_entries,
                                         ignored_entries_list)

    def _entry_pushed(self, entry, error):
        self.view.pushed_entry(entry, error)

class EditCommand(BaseTimesheetCommand):
    """
    Usage: edit

    Opens your zebra file in your favourite editor.

    """
    def run(self):
        # Create the file if it does not exist yet
        file.create_file(self.options.file)
        is_top_down = None

        if self.settings.get('auto_add') != Settings.AUTO_ADD_OPTIONS['NO']:
            try:
                t = self.get_timesheet()
            except (UndefinedAliasError, ParseError):
                pass
            else:
                try:
                    is_top_down = self.get_entries_direction()
                except UnknownDirectionError:
                    is_top_down = True

                auto_fill_days = self.settings.get_auto_fill_days()
                if auto_fill_days:
                    t.prefill(auto_fill_days, limit=None,
                              add_to_bottom=is_top_down)

                t.add_date(datetime.date.today(), is_top_down)
                t.save()

        try:
            editor = self.settings.get('editor')
        except NoOptionError:
            editor = None

        file.spawn_editor(self.options.file, editor)

        try:
            t = self.get_timesheet(True)
        except ParseError as e:
            self.view.err(e)
        else:
            self.view.show_status(t.get_entries())

class HelpCommand(BaseCommand):
    """
    YO DAWG you asked for help for the help command. Try to search Google in
    Google instead.

    """
    def __init__(self, application_container):
        super(HelpCommand, self).__init__(application_container)
        self.commands_mapping = application_container.commands_mapping

    def setup(self):
        if len(self.arguments) == 0:
            raise UsageError()
        else:
            self.command = self.arguments[0]

    def run(self):
        if self.command == 'help':
            self.view.command_usage(self)
        else:
            if self.command in self.commands_mapping:
                self.view.command_usage(self.commands_mapping[self.command])
            else:
                self.view.err(u"Command %s doesn't exist." % self.command)

class SearchCommand(BaseCommand):
    """
    Usage: search search_string

    Searches for a project by its name. The letter in the first column indicates
    the status of the project: [N]ot started, [A]ctive, [F]inished, [C]ancelled.

    """
    def validate(self):
        if len(self.arguments) < 1:
            raise UsageError()

    def run(self):
        projects = self.projects_db.search(self.arguments)
        projects = sorted(projects, key=lambda project: project.name.lower())
        self.view.search_results(projects)

class ShowCommand(BaseCommand):
    """
    Usage: show project_id

    Shows the details of the given project_id (you can find it with the search
    command).

    """
    def validate(self):
        if len(self.arguments) < 1:
            raise UsageError()

        try:
            int(self.arguments[0])
        except ValueError:
            raise UsageError("The project id must be a number")

    def setup(self):
        self.project_id = int(self.arguments[0])

    def run(self):
        try:
            project = self.projects_db.get(self.project_id)
        except IOError:
            raise Exception("Error: the projects database file doesn't exist. "
                            "Please run `taxi update` to create it")

        if project is None:
            raise Exception("Error: the project doesn't exist")

        mappings = self.settings.get_reversed_projects()
        self.view.project_with_activities(project, mappings)

class StartCommand(BaseTimesheetCommand):
    """
    Usage: start project_name

    Use it when you start working on the project project_name. This will add the
    project name and the current time to your entries file. When you're
    finished, use the stop command.

    """
    def validate(self):
        if len(self.arguments) != 1:
            raise UsageError()

    def setup(self):
        self.project_name = self.arguments[0]

    def run(self):
        if self.project_name not in self.settings.get_projects().keys():
            raise UndefinedAliasError(self.project_name)

        file.create_file(self.options.file)

        duration = (datetime.datetime.now().time(), None)
        e = Entry(datetime.date.today(), self.project_name, duration, '?')

        try:
            t = self.get_timesheet()
        except ParseError as e:
            self.view.err(e)
        else:
            t.add_entry(e, self.get_entries_direction())
            t.save()

class StatusCommand(BaseTimesheetCommand):
    """
    Usage: status

    Shows the summary of what's going to be committed to the server.

    """

    def setup(self):
        self.date = self.options.date

    def run(self):
        try:
            t = self.get_timesheet()
        except ParseError as e:
            self.view.err(e)
        else:
            self.view.show_status(t.get_entries(self.date))

class StopCommand(BaseTimesheetCommand):
    """
    Usage: stop [description]

    Use it when you stop working on the current task. You can add a description
    to what you've done.

    """
    def setup(self):
        if len(self.arguments) == 0:
            self.description = None
        else:
            self.description = ' '.join(self.arguments)

    def run(self):
        try:
            t = self.get_timesheet()
            t.continue_entry(datetime.date.today(), datetime.datetime.now().time(),
                             self.description)
        except ParseError as e:
            self.view.err(e)
        except NoActivityInProgressError:
            self.view.err(u"You don't have any activity in progress for today")
        else:
            t.save()

class UpdateCommand(BaseCommand):
    """
    Usage: update

    Synchronizes your project database with the server.

    """
    def setup(self):
        self.site = self.settings.get('site')
        self.username = self.settings.get('username')
        self.password = self.settings.get('password')

    def run(self):
        self.view.updating_projects_database()

        r = remote.ZebraRemote(self.site, self.username, self.password)
        projects = r.get_projects()
        self.projects_db.update(projects)

        self.view.projects_database_update_success()
