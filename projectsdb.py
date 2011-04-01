import json

from remote import ZebraRemote

class ProjectsDb:
    def __init__(self, base_url, username, password):
        self.remote = ZebraRemote(base_url, username, password)

    def update(self):
        self.remote.get_projects()

    def search(self):
        pass
