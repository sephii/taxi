from __future__ import unicode_literals

from . import BaseBackend


class DummyBackend(BaseBackend):
    def authenticate(self):
        pass

    def push_entry(self, date, entry):
        print(entry)

    def get_projects(self):
        return []
