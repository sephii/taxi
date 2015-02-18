from __future__ import unicode_literals

import six

from ..alias import Mapping
from ..backends.registry import backends_registry
from .base import BaseCommand


class UpdateCommand(BaseCommand):
    """
    Usage: update

    Synchronizes your project database with the server and updates the shared
    aliases.

    """
    def run(self):
        self.view.updating_projects_database()

        projects = []

        for backend_name, backend_uri in self.settings.get_backends():
            backend = backends_registry[backend_name]
            backend_projects = backend.get_projects()

            for project in backend_projects:
                project.backend = backend_name

            projects += backend_projects

        self.projects_db.update(projects)

        # Put the shared aliases in the config file
        shared_aliases = {}
        backends_to_clear = set()
        for project in projects:
            if project.is_active():
                for alias, activity_id in six.iteritems(project.aliases):
                    mapping = Mapping(mapping=(project.id, activity_id),
                                      backend=project.backend)
                    shared_aliases[alias] = mapping
                    backends_to_clear.add(project.backend)

        for backend in backends_to_clear:
            self.settings.clear_shared_aliases(backend)

        for alias, mapping in shared_aliases.items():
            self.settings.add_shared_alias(alias, mapping)

        aliases_after_update = self.settings.get_aliases()

        self.settings.write_config()

        self.view.projects_database_update_success(aliases_after_update,
                                                   self.projects_db)
