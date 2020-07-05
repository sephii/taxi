from collections import defaultdict
import inspect
import re

import click

from ..aliases import aliases_database, Mapping
from ..utils import date as date_utils, terminal
from ..exceptions import CancelException
from ..projects import Project


def echo(message):
    click.echo(message)


def echo_error(message):
    echo(click.style(
        click.wrap_text("Error: %s" % message, preserve_paragraphs=True),
        fg='red')
    )


def echo_warning(message):
    echo(click.style(
        click.wrap_text(message, preserve_paragraphs=True),
        fg='yellow')
    )


def echo_success(message):
    echo(click.style(
        click.wrap_text(message, preserve_paragraphs=True),
        fg='green')
    )


class BaseUi(object):
    DURATION_FORMAT = '{:>5.2f}'

    def msg(self, message):
        echo(message)

    def err(self, message):
        echo_error(message)

    def warn(self, message):
        echo_warning(message)

    def projects_list(self, projects, numbered=False):
        for (key, project) in enumerate(projects):
            if numbered:
                self.msg("(%d) %4s %s" % (key, project.id, project.name))
            else:
                self.msg("%4s %s" % (key, project.id, project.name))

    def project_with_activities(self, project, numbered_activities=False):
        self.msg(str(project))
        self.msg("\nActivities:")
        mappings = aliases_database.get_reversed_aliases()

        for (key, activity) in enumerate(project.activities):
            mapping = Mapping(mapping=(project.id, activity.id),
                              backend=project.backend)

            if numbered_activities:
                activity_number = '(%d) ' % (key)
            else:
                activity_number = ''

            if mapping in mappings:
                self.msg("%s%4s %s (mapped to %s)" % (activity_number,
                         activity.id, activity.name,
                         mappings[mapping]))
            else:
                self.msg('%s%4s %s' % (activity_number, activity.id,
                                       activity.name))

    def select_project(self, projects):
        if len(projects) > 1:
            try:
                return terminal.select_number(
                    len(projects),
                    "Choose the project (0-%d), (Ctrl-C) to exit: " %
                    (len(projects) - 1)
                )
            except KeyboardInterrupt:
                raise CancelException()
        else:
            self.msg('Selecting unique choice 0\n')
            return 0

    def select_activity(self, activities):
        if len(activities) > 1:
            try:
                return terminal.select_number(
                    len(activities),
                    "Choose the activity (0-%d), (Ctrl-C) to exit: " %
                    (len(activities) - 1)
                )
            except KeyboardInterrupt:
                raise CancelException()
        else:
            self.msg('Selecting unique choice 0\n')
            return 0

    def select_alias(self):
        try:
            return terminal.select_string(
                "Enter the alias for .tksrc (a-z, - and _ allowed), (Ctrl-C)"
                " to exit: ", r'^[\w-]+$')
        except KeyboardInterrupt:
            raise CancelException()

    def overwrite_alias(self, alias, mapping, retry=True):
        if retry:
            choices = 'y/n/R(etry)'
            default_choice = 'r'
            choice_regexp = r'^[ynr]$'
        else:
            choices = 'y/N'
            default_choice = 'n'
            choice_regexp = r'^[yn]$'

        if mapping.mapping:
            mapping_name = Project.tuple_to_str(mapping.mapping)
            s = ("The alias `%s` is already mapped to `%s`.\nDo you want to "
                 "overwrite it [%s]? " % (alias, mapping_name, choices))
        else:
            s = ("The alias `%s` is already mapped locally.\nDo you want to "
                 "overwrite it [%s]? " % (alias, choices))

        overwrite = terminal.select_string(
            s, choice_regexp, re.I, default_choice
        )

        if overwrite == 'n':
            return False
        elif overwrite == 'y':
            return True

        return None

    def alias_added(self, alias, mapping):
        if mapping:
            mapping_name = Project.tuple_to_str(mapping)
            self.msg("The following alias has been added to your "
                     "configuration file: %s = %s" % (alias, mapping_name))
        else:
            self.msg("The following unmapped alias has been added to your "
                     "configuration file: %s" % alias)

    def _show_mapping(self, mapping, project, alias_first=True):
        (alias, mapping) = mapping

        # Handle local aliases
        if not mapping.is_mapped():
            self.msg("[%s] %s -> not mapped" % (mapping.backend, alias))
            return

        mapping_name = Project.tuple_to_str(mapping.mapping)

        if not project:
            project_name = ''
        else:
            if mapping.mapping[1] is None:
                project_name = project.name
                mapping_name = mapping.mapping[0]
            else:
                activity = project.get_activity(mapping.mapping[1])

                if activity is None:
                    project_name = '%s, ?' % (project.name)
                else:
                    project_name = '%s, %s' % (project.name, activity.name)

        if alias_first:
            args = [mapping.backend, alias, mapping_name]
        else:
            args = [mapping.backend, mapping_name, alias]

        args.append(' (%s)' % project_name if project_name else '')
        text = "[%s] %s -> %s%s" % tuple(args)

        if project and project.is_active():
            self.msg(text)
        else:
            self.msg(click.style(text, fg='red'))

    def mapping_detail(self, mapping, project):
        self._show_mapping(mapping, project, False)

    def alias_detail(self, mapping, project):
        self._show_mapping(mapping, project, True)

    def clean_inactive_aliases(self, aliases):
        self.msg("The following aliases are mapped to inactive projects:\n")

        for (mapping, project) in aliases:
            self.alias_detail(mapping, project)

        return click.confirm("Do you want to clean them?")

    def confirm_commit_entries(self, entries_dict):
        self.msg("The following entries will be included in your commit:\n")
        sorted_entries = sorted(entries_dict.items(), key=lambda e: e[0])

        for date, entries in sorted_entries:
            self.msg(date_utils.unicode_strftime(date, '%A %d %B'))

            for entry in entries:
                self.msg(self.entry_to_str(entry))

        return click.confirm("\nAre you sure you want to continue?")

    def ignored_entries_list(self, entries):
        total = 0
        for entry in entries:
            self.msg(self.get_entry_status(entry))
            total += entry.hours

        self.msg(click.style('\n' + self.columnize([
            "Total ignored", self.DURATION_FORMAT.format(total)]
        ), bold=True))

    def failed_entries_list(self, entries):
        total = 0
        for entry in entries:
            self.msg(click.style(
                self.get_entry_status(entry) + " - " + entry.push_error,
                fg='red'
            ))
            total += entry.hours

        self.msg(click.style('\n' + self.columnize([
            "Total failed", self.DURATION_FORMAT.format(total)]
        ), bold=True, fg='red'))

    def get_entry_status(self, entry, additional_info=None):
        status = [flag for flag in entry.flags]

        if entry.alias not in aliases_database:
            status.append('inexistent alias')

        if status:
            project_name = '%s (%s)' % (entry.alias, ', '.join(status))
        else:
            project_name = entry.alias

        duration_format = self.DURATION_FORMAT
        # Put parentheses around internal aliases since they don't count in the
        # hours total
        if (entry.alias in aliases_database and
                not aliases_database[entry.alias].is_mapped()):
            duration_format = '(' + duration_format + ')'

        description = '{} ({})'.format(entry.description, additional_info) if additional_info else entry.description

        return self.columnize([
            project_name, duration_format.format(entry.hours), description
        ])

    def columnize(self, text):
        for _ in range(len(text), 3):
            text.append('')

        return '{:<30}{:^7} {}'.format(*text)

    def show_status(self, entries_dict):
        if not list(filter(None, entries_dict.values())):
            self.msg("No staging changes. Run `taxi edit` to add entries.")
            return

        self.msg('Staging changes :\n')
        entries_list = entries_dict.items()
        entries_list = sorted(entries_list)
        total_hours = 0

        for (date, entries) in entries_list:
            if len(entries) == 0:
                continue

            subtotal_hours = 0
            # The encoding of date.strftime output depends on the current
            # locale, so we decode it to get a unicode string
            current_date = date_utils.unicode_strftime(date, '%A %d %B').capitalize()

            self.msg(click.style(
                '%s\n' % (current_date),
                bold=True
            ))
            for entry in entries:
                if (not entry.ignored and entry.alias not in
                        aliases_database):
                    self.msg(click.style(
                        self.get_entry_status(entry), fg='yellow'
                    ))

                    close_matches = aliases_database.get_close_matches(
                        entry.alias
                    )
                    if close_matches:
                        self.msg(click.style(
                            '\tDid you mean one of the following: %s?' %
                            ', '.join(close_matches), fg='yellow'
                        ))
                else:
                    self.msg(self.get_entry_status(entry))

                if (entry.alias not in aliases_database or
                        aliases_database[entry.alias].mapping is not None):
                    subtotal_hours += entry.hours or 0

            self.msg(self.columnize([
                '', self.DURATION_FORMAT.format(subtotal_hours)
            ]))
            total_hours += subtotal_hours

        self.msg("\n" + click.style(self.columnize([
            "Total", self.DURATION_FORMAT.format(total_hours)
        ]), bold=True))
        self.msg('\nUse `taxi ci` to commit staging changes to the server')

    def pushed_entry(self, entry, additional_info=None):
        if entry.push_error is not None:
            self.msg(click.style("%s - Failed, reason: %s" % (
                self.get_entry_status(entry),
                entry.push_error
            ), fg='red', bold=True))
        else:
            self.msg(self.get_entry_status(entry, additional_info))

    def entry_to_str(self, entry):
        if entry.ignored:
            alias = u'%s (ignored)' % entry.alias
        else:
            alias = entry.alias

        return '%-30s %-5.2f %s' % (alias, entry.hours, entry.description)

    def pushed_entries_summary(self, entries, ignored_entries):
        backends_total = defaultdict(int)
        for entry in entries:
            if entry.push_error is None:
                backends_total[aliases_database[entry.alias].backend] += entry.hours

        failed_entries = list(
            filter(lambda e: e.push_error is not None, entries)
        )

        self.msg('')
        for backend_name, total in backends_total.items():
            self.msg(click.style(self.columnize([
                "Total pushed, " + backend_name,
                self.DURATION_FORMAT.format(total)
            ]), bold=True))

        if ignored_entries:
            self.msg(click.style("\nIgnored entries\n",
                     fg='yellow', bold=True))
            self.ignored_entries_list(ignored_entries)

        if failed_entries:
            self.msg(click.style("\nFailed entries\n",
                     fg='red', bold=True))
            self.failed_entries_list(failed_entries)

    def pushing_entries(self):
        self.msg("Pushing entries...\n")

    def search_results(self, projects):
        for project in projects:
            self.msg('%s [%s] %4s %s' % (
                project.get_short_status(), project.backend, project.id,
                project.name
            ))

    def suggest_aliases(self, not_found_alias, aliases):
        self.err("The alias `%s` is not mapped in your configuration file." %
                 not_found_alias)

        if len(aliases) > 0:
            self.msg("Did you mean one of the following?\n\n\t%s" %
                     "\n\t".join(aliases))

    def command_usage(self, command):
        self.msg(inspect.getdoc(command))

    def updating_projects_database(self):
        self.msg("Updating database, this may take some time...")

    def projects_database_update_success(self, aliases_after_update,
                                         projects_db):
        """
        Display the results of the projects/aliases database update. We need
        the projects db to extract the name of the projects / activities.
        """
        def show_aliases(aliases):
            """
            Display the given list of aliases in the following form:

            my_alias
                project name / activity name

            The aliases parameter is just a list of aliases, the mapping is
            extracted from the aliases_after_update parameter, and the
            project/activity names are looked up in the projects db.
            """
            for alias in aliases:
                mapping = aliases_after_update[alias]
                (project, activity) = projects_db.mapping_to_project(mapping)

                self.msg("%s\n\t%s / %s" % (
                    alias, project.name if project else "?",
                    activity.name if activity else "?"
                ))

        self.msg("Projects database updated successfully.")

        deleted_aliases = (set(aliases_database.aliases.keys()) -
                           set(aliases_after_update.keys()))
        added_aliases = (set(aliases_after_update.keys()) -
                         set(aliases_database.aliases.keys()))

        modified_aliases = set()
        for alias, mapping in aliases_after_update.items():
            if (alias in aliases_database
                    and aliases_database[alias].mapping
                    and aliases_database[alias].mapping[:2] != mapping.mapping[:2]):
                modified_aliases.add(alias)

        if added_aliases:
            self.msg("\nThe following shared aliases have been added:\n")
            show_aliases(added_aliases)

        if deleted_aliases:
            self.msg("\nThe following shared aliases have been removed:\n")
            for alias in deleted_aliases:
                self.msg(alias)

        if modified_aliases:
            self.msg("\nThe following shared aliases have been updated:\n")
            show_aliases(modified_aliases)

    def show_command_results(self, search, matches, projects_db):
        def mapping_to_activity_name(mapping):
            activity = projects_db.mapping_to_project(mapping)
            if not activity[0] or not activity[1]:
                activity_str = "a non-existent activity"
            else:
                activity_str = '{}, {}'.format(
                    activity[0].name, activity[1].name
                )

            return activity_str

        matches_str = []

        for alias in matches['aliases']:
            if not alias.is_mapped():
                matches_str.append("a local alias")
            else:
                activity_str = mapping_to_activity_name(alias)
                matches_str.append(
                    "an alias to {activity} ({mapping}) on the {backend} "
                    "backend".format(
                        activity=click.style(activity_str, bold=True),
                        mapping=Project.tuple_to_str(alias.mapping),
                        backend=click.style(alias.backend, bold=True)
                    )
                )
        for project, activity in matches['projects']:
            if activity:
                matches_str.append(
                    "the activity {activity} of the project {project}".format(
                        project=click.style(project.name, bold=True),
                        activity=click.style(activity.name, bold=True)
                    )
                )
            else:
                matches_str.append("the project {}".format(
                    click.style(project.name, bold=True)
                ))

        for mapping, alias in matches['mappings']:
            activity_str = mapping_to_activity_name(mapping)
            matches_str.append(
                "aliased by {alias} on the {backend} backend".format(
                    alias=click.style(alias, bold=True),
                    backend=click.style(mapping.backend, bold=True)
                )
            )

        self.msg("Your search string %s is %s." % (
            click.style(search, bold=True),
            ', '.join(matches_str) if matches_str else "nothing"
        ))
