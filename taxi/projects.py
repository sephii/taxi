# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
import copy
import datetime
import json
import os
import re

import six

from .exceptions import TaxiException


@six.python_2_unicode_compatible
class Project:
    STATUS_NOT_STARTED = 0
    STATUS_ACTIVE = 1
    STATUS_FINISHED = 2
    STATUS_CANCELLED = 3

    STATUSES = {
        STATUS_NOT_STARTED: 'Not started',
        STATUS_ACTIVE: 'Active',
        STATUS_FINISHED: 'Finished',
        STATUS_CANCELLED: 'Cancelled',
    }

    SHORT_STATUSES = {
        STATUS_NOT_STARTED: 'N',
        STATUS_ACTIVE: 'A',
        STATUS_FINISHED: 'F',
        STATUS_CANCELLED: 'C',
    }

    STR_TUPLE_REGEXP = r'^(\d+)(?:/(\d+))?$'

    def __init__(self, id, name, status=None, description=None, budget=None):
        self.id = int(id)
        self.name = name
        self.activities = []
        self.status = int(status) if status is not None else None
        self.description = description
        self.budget = budget
        self.aliases = {}
        self.start_date = None
        self.end_date = None
        self.backend = None

    def __str__(self):
        if self.status in self.STATUSES:
            status = self.STATUSES[self.status]
        else:
            status = 'Unknown'

        start_date = self.get_formatted_date(self.start_date)
        if start_date is None:
            start_date = 'Unknown'

        end_date = self.get_formatted_date(self.end_date)
        if end_date is None:
            end_date = 'Unknown'

        return """Id: %s
Name: %s
Status: %s
Start date: %s
End date: %s
Budget: %s
Description: %s""" % (self.id, self.name, status, start_date, end_date,
                      self.budget, self.description)

    def get_formatted_date(self, date):
        if date is not None:
            try:
                formatted_date = date.strftime('%d.%m.%Y')
            except ValueError:
                formatted_date = None
        else:
            formatted_date = None

        return formatted_date

    def add_activity(self, activity):
        self.activities.append(activity)

    def get_activity(self, id):
        for activity in self.activities:
            if activity.id == id:
                return activity

        return None

    def is_active(self):
        return (self.status == self.STATUS_ACTIVE and
                (self.start_date is None or
                    self.start_date <= datetime.date.today()) and
                (self.end_date is None or self.end_date >=
                    datetime.date.today()))

    def get_short_status(self):
        if self.status not in self.SHORT_STATUSES:
            return '?'

        return self.SHORT_STATUSES[self.status]

    @classmethod
    def str_to_tuple(cls, string):
        """
        Converts a string in the format xxx/yyy to a (project, activity)
        tuple

        """
        matches = re.match(cls.STR_TUPLE_REGEXP, string)

        if not matches or len(matches.groups()) != 2:
            return None

        return tuple(
            [int(item) if item else None for item in matches.groups()]
        )

    @classmethod
    def tuple_to_str(cls, t):
        """
        Converts a (project, activity) tuple to a string in the format
        xxx/yyy

        """
        if len(t) != 2:
            return None

        if t[1] is not None:
            return u'%s/%s' % t
        else:
            return six.text_type(t[0])


class Activity:
    def __init__(self, id, name, price):
        self.id = int(id)
        self.name = name
        self.price = price


class ProjectsDb:
    PROJECTS_FILE = 'projects.json'

    def __init__(self, path):
        self.path = path
        self.projects_database_file = os.path.join(self.path,
                                                   self.PROJECTS_FILE)
        self._projects_by_id_cache = None
        self._projects_cache = None

    def get_projects(self):
        if self._projects_cache is not None:
            return self._projects_cache

        try:
            if not os.stat(self.projects_database_file).st_size:
                return []
        # If the db file doesn't exist (eg. ``taxi update`` not run), return an
        # empty list
        except OSError:
            return []

        with open(self.projects_database_file, 'r') as projects_db:
            try:
                lpdb = json.load(projects_db, cls=LocalProjectsDbDecoder)
            # Pre-4.0 used a pickle-based format for the projects db
            except (UnicodeDecodeError, ValueError):
                raise OutdatedProjectsDbException()

        if lpdb.VERSION < LocalProjectsDb.VERSION:
            raise OutdatedProjectsDbException()

        self._projects_cache = lpdb.projects

        return lpdb.projects

    def update(self, projects):
        lpdb = LocalProjectsDb(projects)

        with open(self.projects_database_file, 'w') as output:
            json.dump(lpdb.get_dump_object(), output)

        self._projects_cache = None
        self._projects_by_id_cache = None

    def search(self, search, active_only=False, backend=None):
        projects = self.get_projects()
        found_list = []

        for project in projects:
            found = True

            for s in search:
                s = s.lower()
                found = (project.name.lower().find(s) > -1 or
                         str(project.id) == s)

                if not found:
                    break

            found = found and (backend is None or project.backend ==
                               backend)

            if found:
                if not active_only or project.is_active():
                    found_list.append(project)

        return found_list

    def get(self, id, backend=None):
        if self._projects_by_id_cache is None:
            projects = self.get_projects()
            self._projects_by_id_cache = defaultdict(list)

            for project in projects:
                self._projects_by_id_cache[project.id].append(project)

        for project in self._projects_by_id_cache.get(id, []):
            if backend is None or project.backend == backend:
                return project

        return None

    def mapping_to_project(self, mapping):
        project = self.get(mapping.mapping[0], mapping.backend)

        if not project:
            return (None, None)

        activity = project.get_activity(mapping.mapping[1])

        if not activity:
            return (project, None)

        return (project, activity)


class LocalProjectsDb:
    VERSION = 2

    def __init__(self, projects=None):
        if not projects:
            projects = []

        self.projects = projects

    def get_dump_object(self):
        return {
            'VERSION': self.VERSION,
            'projects': [
                self.dump_project(project) for project in self.projects
            ]
        }

    def dump_project(self, project):
        project_dict = copy.copy(project.__dict__)

        for date_type in ['start_date', 'end_date']:
            if project_dict[date_type] is not None:
                project_dict[date_type] = project_dict[date_type].isoformat()

        project_dict['activities'] = [
            activity.__dict__ for activity in project_dict['activities']
        ]

        return project_dict


class LocalProjectsDbDecoder(json.JSONDecoder):
    def decode(self, s):
        s = super(LocalProjectsDbDecoder, self).decode(s)

        projects = s['projects']
        projects_copy = []
        for project in projects:
            project['activities'] = [
                Activity(activity['id'], activity['name'], activity['price'])
                for activity in project['activities']
            ]
            for date_type in ['start_date', 'end_date']:
                if project[date_type] is not None:
                    project[date_type] = datetime.datetime.strptime(
                        project[date_type], '%Y-%m-%d').date()

            p_copy = Project(project['id'], project['name'])
            p_copy.__dict__.update(project)
            projects_copy.append(p_copy)

        lpdb = LocalProjectsDb(projects_copy)
        lpdb.VERSION = s['VERSION']

        return lpdb


class OutdatedProjectsDbException(TaxiException):
    def __init__(self, *args, **kwargs):
        self.message = (
            "Your projects db is outdated, please run `taxi update` to update"
            " it"
        )

        super(OutdatedProjectsDbException, self).__init__(self.message,
                                                          *args, **kwargs)
