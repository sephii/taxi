from __future__ import unicode_literals

from ..exceptions import UsageError
from .base import BaseCommand


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
