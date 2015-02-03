# -*- coding: utf-8 -*-
from ConfigParser import NoOptionError
import calendar
import datetime

from taxi import remote
from taxi.exceptions import CancelException, UsageError
from taxi.projects import Project
from taxi.timesheet import (
    NoActivityInProgressError, Timesheet, TimesheetCollection, TimesheetFile
)
from taxi.timesheet.entry import TimesheetEntry, EntriesCollection
from taxi.timesheet.parser import ParseError
from taxi.settings import Settings
from taxi.utils import file
from taxi.utils.structures import OrderedSet


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
    def get_timesheet_collection(self, skip_cache=False):
        timesheet_collection = getattr(self, '_current_timesheet_collection',
                                       None)
        if timesheet_collection is not None and not skip_cache:
            return timesheet_collection

        timesheet_collection = TimesheetCollection()

        timesheet_files = self.get_files(
            self.options['unparsed_file'],
            int(self.settings.get('nb_previous_files'))
        )

        self.alias_mappings = self.settings.get_aliases()

        for file_path in timesheet_files:
            timesheet_file = TimesheetFile(file_path)
            try:
                timesheet_contents = timesheet_file.read()
            except IOError:
                timesheet_contents = ''

            t = Timesheet(
                EntriesCollection(
                    timesheet_contents,
                    self.settings.get('date_format')
                ),
                self.alias_mappings,
                timesheet_file
            )

            # Force new entries direction if necessary
            if (self.settings.get('auto_add') in [
                    Settings.AUTO_ADD_OPTIONS['TOP'],
                    Settings.AUTO_ADD_OPTIONS['BOTTOM']]):
                t.entries.add_date_to_bottom = (
                    self.settings.get('auto_add') ==
                    Settings.AUTO_ADD_OPTIONS['BOTTOM']
                )

            timesheet_collection.timesheets.append(t)

        # Fix `add_date_to_bottom` attribute of timesheet entries based on
        # previous timesheets. When a new timesheet is started it won't have
        # any direction defined, so we take the one from the previous
        # timesheet, if any
        previous_timesheet = None
        for timesheet in reversed(timesheet_collection.timesheets):
            if (timesheet.entries.add_date_to_bottom is None
                    and previous_timesheet
                    and previous_timesheet.entries.add_date_to_bottom
                    is not None):
                timesheet.entries.add_date_to_bottom = (
                    previous_timesheet.entries.add_date_to_bottom
                )
            previous_timesheet = timesheet

        setattr(self, '_current_timesheet_collection', timesheet_collection)

        return timesheet_collection

    def get_files(self, filename, nb_previous_files):
        date_units = ['m', 'Y']
        smallest_unit = None

        for date in date_units:
            if '%%%s' % date in filename:
                smallest_unit = date
                break

        if smallest_unit is None:
            return OrderedSet([filename])

        files = OrderedSet()
        file_date = datetime.date.today()
        for i in xrange(0, nb_previous_files + 1):
            files.add(file.expand_filename(filename, file_date))

            if smallest_unit == 'm':
                if file_date.month == 1:
                    file_date = file_date.replace(day=1,
                                                  month=12,
                                                  year=file_date.year - 1)
                else:
                    file_date = file_date.replace(day=1,
                                                  month=file_date.month - 1)

            elif smallest_unit == 'Y':
                file_date = file_date.replace(day=1, year=file_date.year - 1)

        return files


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
            self.view.msg(
                u"No active project matches your search string '%s'" %
                ''.join(search)
            )
            return

        self.view.projects_list(projects, True)

        try:
            number = self.view.select_project(projects)
        except CancelException:
            return

        project = projects[number]
        mappings = self.settings.get_reversed_aliases()
        self.view.project_with_activities(project, mappings,
                                          numbered_activities=True)

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

            if self.settings.activity_exists(alias):
                mapping = self.settings.get_aliases()[alias]
                overwrite = self.view.overwrite_alias(alias, mapping)

                if not overwrite:
                    return
                elif overwrite:
                    retry = False
                # User chose "retry"
                else:
                    retry = True
            else:
                retry = False

        activity = project.activities[number]
        self.settings.add_alias(alias, project.id, activity.id)
        self.settings.write_config()

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

    You can also run this command without any argument to view all your
    mappings.

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
                self.view.alias_detail(
                    m,
                    self.projects_db.get(m[1][0]) if m[1] is not None else None
                )

    def _add_alias(self, alias_name, mapping):
        project_activity = Project.str_to_tuple(mapping)

        if project_activity is None:
            raise UsageError("The mapping must be in the format xxxx/yyyy")

        if self.settings.activity_exists(alias_name):
            existing_mapping = self.settings.get_aliases()[alias_name]
            confirm = self.view.overwrite_alias(alias_name, existing_mapping,
                                                False)

            if not confirm:
                return

        self.settings.add_alias(alias_name, project_activity[0],
                                project_activity[1])
        self.settings.write_config()

        self.view.alias_added(alias_name, project_activity)


class AutofillCommand(BaseTimesheetCommand):
    """
    Usage: autofill

    Fills your timesheet up to today, for the defined auto_fill_days.

    """
    def run(self):
        auto_fill_days = self.settings.get_auto_fill_days()

        if auto_fill_days:
            today = datetime.date.today()
            last_day = calendar.monthrange(today.year, today.month)
            last_date = datetime.date(today.year, today.month, last_day[1])

            timesheet_collection = self.get_timesheet_collection()
            t = timesheet_collection.timesheets[0]
            t.prefill(auto_fill_days, last_date)
            t.file.write(t.entries)

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
        aliases = self.settings.get_aliases()
        inactive_aliases = []

        for (alias, mapping) in aliases.iteritems():
            # Ignore local aliases
            if mapping is None:
                continue

            project = self.projects_db.get(mapping[0])

            if (project is None or not project.is_active() or
                    (mapping[1] is not None
                     and project.get_activity(mapping[1]) is None)):
                inactive_aliases.append(((alias, mapping), project))

        if not inactive_aliases:
            self.view.msg(u"No inactive aliases found.")
            return

        if not self.options.get('force_yes'):
            confirm = self.view.clean_inactive_aliases(inactive_aliases)

        if self.options.get('force_yes') or confirm:
            self.settings.remove_aliases(
                [item[0][0] for item in inactive_aliases]
            )
            self.settings.write_config()
            self.view.msg(u"%d inactive aliases have been successfully"
                          " cleaned." % len(inactive_aliases))


class CommitCommand(BaseTimesheetCommand):
    """
    Usage: commit

    Commits your work to the server.

    """
    def run(self):
        timesheet_collection = self.get_timesheet_collection()

        if (self.options.get('date', None) is None
                and not self.options.get('ignore_date_error', False)):
            non_workday_entries = (
                timesheet_collection.get_non_current_workday_entries()
            )

            if non_workday_entries:
                self.view.non_working_dates_commit_error(
                    non_workday_entries.keys()
                )

                return

        self.view.pushing_entries()
        r = remote.ZebraRemote(self.settings.get('site'),
                               self.settings.get('username'),
                               self.settings.get('password'))

        all_pushed_entries = []
        all_failed_entries = []

        for timesheet in timesheet_collection.timesheets:
            entries_to_push = timesheet.get_entries(
                self.options.get('date', None), exclude_ignored=True,
                exclude_local=True, exclude_unmapped=True, regroup=True
            )

            (pushed_entries, failed_entries) = r.send_entries(
                entries_to_push, self.alias_mappings, self._entry_pushed
            )

            local_entries = timesheet.get_local_entries(
                self.options.get('date', None)
            )
            local_entries_list = []
            for (date, entries) in local_entries.iteritems():
                local_entries_list.extend(entries)

            for entry in local_entries_list + pushed_entries:
                entry.commented = True

            for (entry, _) in failed_entries:
                entry.fix_start_time()

            # Also fix start time for ignored entries. Since they won't get
            # pushed, there's a chance their previous sibling gets commented
            for (date, entries) in timesheet.get_ignored_entries().items():
                for entry in entries:
                    entry.fix_start_time()

            timesheet.file.write(timesheet.entries)

            all_pushed_entries.extend(pushed_entries)
            all_failed_entries.extend(failed_entries)

        ignored_entries = timesheet_collection.get_ignored_entries(
            self.options.get('date', None)
        )
        ignored_entries_list = []
        for (date, entries) in ignored_entries.iteritems():
            ignored_entries_list.extend(entries)

        self.view.pushed_entries_summary(all_pushed_entries,
                                         all_failed_entries,
                                         ignored_entries_list)

    def _entry_pushed(self, entry, error):
        self.view.pushed_entry(entry, error, self.alias_mappings)


class EditCommand(BaseTimesheetCommand):
    """
    Usage: edit

    Opens your zebra file in your favourite editor.

    """
    def run(self):
        timesheet_collection = None

        try:
            timesheet_collection = self.get_timesheet_collection()
        except ParseError:
            pass

        if timesheet_collection:
            t = timesheet_collection.timesheets[0]

            if (self.settings.get('auto_add') !=
                    Settings.AUTO_ADD_OPTIONS['NO']
                    and not self.options.get('forced_file')):
                auto_fill_days = self.settings.get_auto_fill_days()
                if auto_fill_days:
                    t.prefill(auto_fill_days, limit=None)

                t.file.write(t.entries)

        try:
            editor = self.settings.get('editor')
        except NoOptionError:
            editor = None

        file.spawn_editor(self.options['file'], editor)

        try:
            timesheet_collection = self.get_timesheet_collection(True)
        except ParseError as e:
            self.view.err(e)
        else:
            self.view.show_status(
                timesheet_collection.get_entries(regroup=True),
                self.alias_mappings, self.settings
            )


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

    Searches for a project by its name. The letter in the first column
    indicates the status of the project: [N]ot started, [A]ctive, [F]inished,
    [C]ancelled.

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
            self.view.err(
                u"The project `%s` doesn't exist" % (self.project_id)
            )
        else:
            mappings = self.settings.get_reversed_aliases()
            self.view.project_with_activities(project, mappings)


class StartCommand(BaseTimesheetCommand):
    """
    Usage: start project_name

    Use it when you start working on the project project_name. This will add
    the project name and the current time to your entries file. When you're
    finished, use the stop command.

    """
    def validate(self):
        if len(self.arguments) != 1:
            raise UsageError()

    def setup(self):
        self.project_name = self.arguments[0]

    def run(self):
        today = datetime.date.today()

        try:
            timesheet_collection = self.get_timesheet_collection()
        except ParseError as e:
            self.view.err(e)
            return

        t = timesheet_collection.timesheets[0]

        # If there's a previous entry on the same date, check if we can use its
        # end time as a start time for the newly started entry
        today_entries = t.get_entries(today)
        if(today in today_entries and today_entries[today]
                and isinstance(today_entries[today][-1].duration, tuple)
                and today_entries[today][-1].duration[1] is not None):
            new_entry_start_time = today_entries[today][-1].duration[1]
        else:
            new_entry_start_time = datetime.datetime.now()

        duration = (new_entry_start_time, None)
        e = TimesheetEntry(self.project_name, duration, '?')
        t.entries[today].append(e)
        t.file.write(t.entries)


class StatusCommand(BaseTimesheetCommand):
    """
    Usage: status

    Shows the summary of what's going to be committed to the server.

    """

    def setup(self):
        self.date = self.options.get('date', None)

    def run(self):
        try:
            timesheet_collection = self.get_timesheet_collection()
        except ParseError as e:
            self.view.err(e)
        else:
            self.view.show_status(
                timesheet_collection.get_entries(self.date, regroup=True),
                self.alias_mappings,
                self.settings
            )


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
            timesheet_collection = self.get_timesheet_collection()
            current_timesheet = timesheet_collection.timesheets[0]
            current_timesheet.continue_entry(
                datetime.date.today(),
                datetime.datetime.now().time(),
                self.description
            )
        except ParseError as e:
            self.view.err(e)
        except NoActivityInProgressError:
            self.view.err(u"You don't have any activity in progress for today")
        else:
            current_timesheet.file.write(current_timesheet.entries)


class UpdateCommand(BaseCommand):
    """
    Usage: update

    Synchronizes your project database with the server and updates the shared
    aliases.

    """
    def setup(self):
        self.site = self.settings.get('site')
        self.username = self.settings.get('username')
        self.password = self.settings.get('password')

    def run(self):
        self.view.updating_projects_database()

        aliases_before_update = self.settings.get_aliases()
        local_aliases = self.settings.get_aliases(include_shared=False)

        r = remote.ZebraRemote(self.site, self.username, self.password)
        projects = r.get_projects()
        self.projects_db.update(projects)

        # Put the shared aliases in the config file
        shared_aliases = {}
        for project in projects:
            if project.is_active():
                for alias, activity_id in project.aliases.iteritems():
                    self.settings.add_shared_alias(alias, project.id,
                                                   activity_id)
                    shared_aliases[alias] = (project.id, activity_id)

        aliases_after_update = self.settings.get_aliases()

        self.settings.write_config()

        self.view.projects_database_update_success(aliases_before_update,
                                                   aliases_after_update,
                                                   local_aliases,
                                                   shared_aliases,
                                                   self.projects_db)
