import json
import pickle
import os

from remote import ZebraRemote
from settings import settings

class ProjectsDb:
    DB_PATH = 'projects.db'

    def _get_projects(self):
        input = open(os.path.join(settings.TAXI_PATH, self.DB_PATH), 'r')
        return pickle.load(input)

    def update(self, base_url, username, password):
        remote = ZebraRemote(base_url, username, password)
        print 'Updating database, this may take some time...'
        projects = remote.get_projects()

        output = open(os.path.join(settings.TAXI_PATH, self.DB_PATH), 'w')
        pickle.dump(projects, output)

    def search(self, search):
        projects = self._get_projects()
        found_list = []
        search = search.lower()

        for project in projects:
            if project.name.lower().find(search) > -1:
                found_list.append(project)

        return found_list

    def get(self, id):
        projects = self._get_projects()
        found_list = []
        id = int(id)

        for project in projects:
            if project.id == id:
                return project

        raise Exception('Project not found')
