# -*- coding: utf-8 -*-
import datetime
import pickle
import re

from taxi.exceptions import TaxiException


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

    STR_TUPLE_REGEXP = r'^(\d{1,4})(?:/(\d{1,4}))?$'

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

    def __unicode__(self):
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

        return u"""Id: %s
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
                    self.start_date <= datetime.datetime.now()) and
                (self.end_date is None or self.end_date >=
                    datetime.datetime.now()))

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
            return unicode(t[0])


class Activity:
    def __init__(self, id, name, price):
        self.id = int(id)
        self.name = name
        self.price = price


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
                raise TaxiException("Your projects db is out of date, please"
                                    " run `taxi update` to update it")

            if (not isinstance(lpdb, LocalProjectsDb)
                    or lpdb.VERSION < LocalProjectsDb.VERSION):
                raise TaxiException("Your projects db is out of date, please"
                                    " run `taxi update` to update it")

            setattr(self, '_projects_cache', lpdb.projects)

            return lpdb.projects
        except (IOError, EOFError):
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
