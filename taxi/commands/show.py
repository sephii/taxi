from __future__ import unicode_literals

from ..exceptions import UsageError
from .base import BaseCommand


class ShowCommand(BaseCommand):
    """
    Usage: show project_id [backend]

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
        self.backend = self.arguments[1] if len(self.arguments) > 1 else None

    def run(self):
        try:
            project = self.projects_db.get(self.project_id, self.backend)
        except IOError:
            raise Exception("Error: the projects database file doesn't exist. "
                            "Please run `taxi update` to create it")

        if project is None:
            self.view.err(
                "Could not find project `%s`" % (self.project_id)
            )
        else:
            self.view.project_with_activities(project)
