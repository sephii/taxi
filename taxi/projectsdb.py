# -*- coding: utf-8 -*-
import json
import pickle
import os

from remote import ZebraRemote
from settings import settings

class ProjectsDb:
    DB_PATH = 'projects.db'

    def _get_projects(self):
        projects_cache = getattr(self, '_projects_cache', None)
        if projects_cache is not None:
            return projects_cache

        try:
            input = open(os.path.join(settings.TAXI_PATH, self.DB_PATH), 'r')

            try:
                lpdb = pickle.load(input)
            except ImportError:
                raise Exception('Your projects db is out of date, please '
                        'run `taxi update` to update it')

            if not isinstance(lpdb, LocalProjectsDb) or lpdb.VERSION < LocalProjectsDb.VERSION:
                raise Exception('Your projects db is out of date, please' \
                        ' run `taxi update` to update it')

            setattr(self, '_projects_cache', lpdb.projects)

            return lpdb.projects
        except IOError:
            raise Exception('Error: the projects database file doesn\'t exist.  Please run `taxi update` to create it')

    def update(self, base_url, username, password):
        remote = ZebraRemote(base_url, username, password)
        print(u'Updating database, this may take some time...')
        projects = remote.get_projects()
        lpdb = LocalProjectsDb(projects)

        output = open(os.path.join(settings.TAXI_PATH, self.DB_PATH), 'w')
        pickle.dump(lpdb, output)

        print(u'Projects database updated successfully')

    def search(self, search, active_only=False):
        projects = self._get_projects()
        found_list = []

        for project in projects:
            found = True

            for s in search:
                s = s.lower()
                found = project.name.lower().find(s) > -1

                if not found:
                    break

            if found:
                if not active_only or project.is_active():
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

class LocalProjectsDb:
    projects = []
    VERSION = 2

    def __init__(self, projects):
        self.projects = projects
