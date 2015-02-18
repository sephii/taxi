from __future__ import unicode_literals

from ..alias import alias_database, Mapping
from ..exceptions import CancelException, UsageError
from .base import BaseCommand


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
                "No active project matches your search string '%s'" %
                ''.join(search)
            )
            return

        self.view.projects_list(projects, True)

        try:
            number = self.view.select_project(projects)
        except CancelException:
            return

        project = projects[number]
        self.view.project_with_activities(project, numbered_activities=True)

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

            if alias in alias_database:
                mapping = alias_database[alias]
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
        mapping = Mapping(mapping=(project.id, activity.id),
                          backend=project.backend)
        self.settings.add_alias(alias, mapping)
        self.settings.write_config()

        self.view.alias_added(alias, (project.id, activity.id))
