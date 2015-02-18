from __future__ import unicode_literals

from ..alias import alias_database, Mapping
from ..exceptions import UsageError
from ..projects import Project
from .base import BaseCommand


class AliasCommand(BaseCommand):
    """
    Usage: alias [alias]
           alias [project_id]
           alias [project_id/activity_id]
           alias [alias] [project_id/activity_id] [backend]

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
        if len(self.arguments) not in [0, 1, 3]:
            raise UsageError()

    def setup(self):
        if len(self.arguments) == 3:
            self.alias = self.arguments[0]
            mapping = Project.str_to_tuple(self.arguments[1])
            if mapping is None:
                raise UsageError("The mapping must be in the format xxxx/yyyy")

            self.mapping = Mapping(mapping=mapping, backend=self.arguments[2])
            self.mode = self.MODE_ADD_ALIAS
        elif len(self.arguments) == 1:
            self.alias = self.arguments[0]
            self.mode = self.MODE_SHOW_MAPPING
        else:
            self.alias = None
            self.mode = self.MODE_LIST_ALIASES

    def run(self):
        # 3 arguments, add a new alias
        if self.mode == self.MODE_ADD_ALIAS:
            self._add_alias(self.alias, self.mapping)
        # 1 argument, display the alias or the project id/activity id tuple
        elif self.mode == self.MODE_SHOW_MAPPING:
            mapping = Project.str_to_tuple(self.alias)

            if mapping is not None:
                for alias, m in alias_database.filter_from_mapping(mapping).items():
                    self.view.mapping_detail(
                        (alias, m.mapping if m is not None else None),
                        self.projects_db.get(m.mapping[0], m.backend)
                        if m is not None else None
                    )
            else:
                self.mode = self.MODE_LIST_ALIASES

        # No argument, display the mappings
        if self.mode == self.MODE_LIST_ALIASES:
            for alias, m in alias_database.filter_from_alias(self.alias).items():
                self.view.alias_detail(
                    (alias, m.mapping if m is not None else None),
                    self.projects_db.get(m.mapping[0], m.backend)
                    if m is not None else None
                )

    def _add_alias(self, alias_name, mapping):
        if alias_name in alias_database:
            existing_mapping = alias_database[alias_name]
            confirm = self.view.overwrite_alias(
                alias_name, existing_mapping, False
            )

            if not confirm:
                return

        self.settings.add_alias(alias_name, mapping)
        self.settings.write_config()

        self.view.alias_added(alias_name, mapping.mapping)
