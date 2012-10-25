import inspect
import re
import sys

from taxi.utils import terminal
from taxi.exceptions import CancelException
from taxi.models import Project

class BaseUi(object):
    def msg(self, message):
        # Encoding is None if the output is piped through another command (eg.
        # grep)
        if sys.stdout.encoding is None:
            encoding = 'UTF-8'
        else:
            encoding = sys.stdout.encoding

        print(message.encode(encoding))

    def err(self, message):
        self.msg(u"Error: %s" % message)

    def projects_list(self, projects, numbered=False):
        for (key, project) in enumerate(projects):
            if numbered:
                self.msg(u"(%d) %4s %s" % (key, project.id, project.name))
            else:
                self.msg(u"%4s %s" % (key, project.id, project.name))

    def project_with_activities(self, project, mappings={}, numbered_activities=False):
        self.msg(unicode(project))
        self.msg(u"\nActivities:")
        for (key, activity) in enumerate(project.activities):
            if numbered_activities:
                activity_number = '(%d) ' % (key)
            else:
                activity_number = ''

            if (project.id, activity.id) in mappings:
                self.msg(u"%s%4s %s (mapped to %s)" % (activity_number,
                         activity.id, activity.name,
                         mappings[(project.id, activity.id)]))
            else:
                self.msg(u'%s%4s %s' % (activity_number, activity.id,
                                         activity.name))

    def select_project(self, projects):
        try:
            return terminal.select_number(len(projects), u"Choose the project "
                                          "(0-%d), (Ctrl-C) to exit: " %
                                          (len(projects) - 1))
        except KeyboardInterrupt:
            raise CancelException()

    def select_activity(self, activities):
        try:
            return terminal.select_number(len(activities), u"Choose the "
                                          "activity (0-%d), (Ctrl-C) to exit: " %
                                          (len(activities) - 1))
        except KeyboardInterrupt:
            raise CancelException()

    def select_alias(self):
        try:
            return terminal.select_string(u"Enter the alias for .tksrc (a-z, - "
                                          "and _ allowed), (Ctrl-C) to exit: ",
                                          r'^[\w-]+$')
        except KeyboardInterrupt:
            raise CancelException()

    def overwrite_alias(self, alias, mapping, retry=True):
        mapping_name = Project.tuple_to_str(mapping)

        if retry:
            choices = 'y/n/R(etry)'
            default_choice = 'r'
            choice_regexp = r'^[ynr]$'
        else:
            choices = 'y/N'
            default_choice = 'n'
            choice_regexp = r'^[yn]$'

        s = (u"The alias `%s` is already mapped to `%s`.\nDo you want to "
             "overwrite it [%s]? " % (alias, mapping_name, choices))

        overwrite = terminal.select_string(s, choice_regexp, re.I, default_choice)

        if overwrite == 'n':
            return False
        elif overwrite == 'y':
            return True

        return None

    def alias_added(self, alias, mapping):
        mapping_name = Project.tuple_to_str(mapping)

        self.msg(u"The following alias has been added to your configuration "
                 "file: %s = %s" % ((alias) + mapping_name))

    def _show_mapping(self, mapping, project, alias_first=True):
        (alias, t) = mapping

        mapping_name = '%s/%s' % t

        if not project:
            project_name = '?'
        else:
            if t[1] is None:
                project_name = project.name
                mapping_name = t[0]
            else:
                activity = project.get_activity(t[1])

                if activity is None:
                    project_name = u'%s, ?' % (project.name)
                else:
                    project_name = u'%s, %s' % (project.name, activity.name)

        if alias_first:
            args = (alias, mapping_name, project_name)
        else:
            args = (mapping_name, alias, project_name)

        self.msg(u"%s -> %s (%s)" % args)

    def mapping_detail(self, mapping, project):
        self._show_mapping(mapping, project, False)

    def alias_detail(self, mapping, project):
        self._show_mapping(mapping, project, True)

    def clean_inactive_aliases(self, aliases):
        self.msg(u"The following aliases are mapped to inactive projects:\n")

        for (mapping, project) in aliases:
            self.alias_detail(mapping, project)

        confirm = terminal.select_string(u"\nDo you want to clean them [y/N]? ",
                                         r'^[yn]$', re.I, 'n')

        return confirm == 'y'

    def pushed_entries_total(self, pushed_entries):
        total_hours = 0
        for entry in pushed_entries:
            total_hours += entry.get_duration()

        self.msg(u'\n%-29s %5.2f' % ('Total pushed', total_hours))

    def ignored_entries_list(self, ignored_entries):
        ignored_hours = 0
        for entry in ignored_entries:
            ignored_hours += entry.get_duration()
            self.msg(unicode(entry))

        self.msg(u'\n%-29s %5.2f' % ('Total ignored', ignored_hours))

    def non_working_dates_commit_error(self, dates):
        dates = [d.strftime('%A %d %B') for d in dates]

        self.err(u"You're trying to commit for a day that's "
        " on a week-end or that's not yesterday nor today (%s).\n"
        "To ignore this error, re-run taxi with the option "
        "`--ignore-date-error`" % ', '.join(dates))

    def show_status(self, entries_list):
        self.msg(u'Staging changes :\n')
        entries_list = sorted(entries_list)
        total_hours = 0

        for (date, entries) in entries_list:
            if len(entries) == 0:
                continue

            subtotal_hours = 0
            self.msg(u'# %s #' % date.strftime('%A %d %B').capitalize())
            for entry in entries:
                self.msg(unicode(entry))
                subtotal_hours += entry.get_duration() or 0

            self.msg(u'%-29s %5.2f\n' % ('', subtotal_hours))
            total_hours += subtotal_hours

        self.msg(u'%-29s %5.2f' % ('Total', total_hours))
        self.msg(u'\nUse `taxi ci` to commit staging changes to the server')

    def pushed_entry(self, entry, error):
        if error:
            self.msg(u"%s - Failed, reason: %s " % (unicode(entry), error))
        else:
            self.msg(unicode(entry))

    def failed_entries_list(self, failed_entries):
        for failed_entry in failed_entries:
            self.msg(u"%s, reason: %s" % failed_entry)

    def pushed_entries_summary(self, pushed_entries, failed_entries,
                               ignored_entries):
        self.pushed_entries_total(pushed_entries)

        if ignored_entries:
            self.msg(u"\nIgnored entries:\n")
            self.ignored_entries_list(ignored_entries)

    def pushing_entries(self):
        self.msg(u"Pushing entries...\n")

    def search_results(self, projects):
        for project in projects:
            self.msg(u'%s %4s %s' % (project.get_short_status(), project.id, project.name))

    def suggest_aliases(self, not_found_alias, aliases):
        self.err(u"The alias `%s` is not mapped in your configuration file." %
                 not_found_alias)

        if len(aliases) > 0:
            self.msg(u"Did you mean one of the following?\n\n\t%s" %
                     "\n\t".join(aliases))

    def command_usage(self, command):
        self.msg(inspect.getdoc(command))

    def updating_projects_database(self):
        self.msg(u"Updating database, this may take some time...")

    def projects_database_update_success(self):
        self.msg(u"Projects database updated successfully.")
