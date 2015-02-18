from __future__ import unicode_literals

import six

from ..alias import alias_database
from .base import BaseCommand


class CleanAliasesCommand(BaseCommand):
    """
    Usage: clean-aliases

    Removes aliases from your config file that point to inactive projects.

    """
    def run(self):
        inactive_aliases = []

        for (alias, mapping) in six.iteritems(alias_database):
            # Ignore local aliases
            if mapping is None:
                continue

            project = self.projects_db.get(mapping.mapping[0], mapping.backend)

            if (project is None or not project.is_active() or
                    (mapping.mapping[1] is not None
                     and project.get_activity(mapping.mapping[1]) is None)):
                inactive_aliases.append(((alias, mapping), project))

        if not inactive_aliases:
            self.view.msg("No inactive aliases found.")
            return

        if not self.options.get('force_yes'):
            confirm = self.view.clean_inactive_aliases(inactive_aliases)

        if self.options.get('force_yes') or confirm:
            self.settings.remove_aliases(
                [item[0] for item in inactive_aliases]
            )
            self.settings.write_config()
            self.view.msg("%d inactive aliases have been successfully"
                          " cleaned." % len(inactive_aliases))
