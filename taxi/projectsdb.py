# -*- coding: utf-8 -*-
import pickle


class ProjectsDb:
    def __init__(self, path):
        self.path = path

    def _get_projects(self):
        projects_cache = getattr(self, '_projects_cache', None)
        if projects_cache is not None:
            return projects_cache

        try:
            input = open(self.path, 'r')

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
            return []

    def update(self, projects):
        lpdb = LocalProjectsDb(projects)

        output = open(self.path, 'w')
        pickle.dump(lpdb, output)

    def search(self, search, active_only=False):
        projects = self._get_projects()
        found_list = []

        for project in projects:
            found = True

            for s in search:
                s = s.lower()
                found = (project.name.lower().find(s) > -1 or
                         str(project.id) == s)

                if not found:
                    break

            if found:
                if not active_only or project.is_active():
                    found_list.append(project)

        return found_list

    def get(self, id):
        projects_hash = getattr(self, '_projects_hash', None)
        if projects_hash is None:
            projects = self._get_projects()
            projects_hash = {}

            for project in projects:
                projects_hash[project.id] = project

            setattr(self, '_projects_hash', projects_hash)

        return projects_hash[id] if id in projects_hash else None

    def mapping_to_project(self, mapping_tuple):
        project = self.get(mapping_tuple[0])

        if not project:
            return (None, None)

        activity = project.get_activity(mapping_tuple[1])

        if not activity:
            return (project, None)

        return (project, activity)

class LocalProjectsDb:
    projects = []
    VERSION = 2

    def __init__(self, projects):
        self.projects = projects
