# -*- coding: utf-8 -*-
import codecs
import ConfigParser
import os
import difflib

class Settings:
    TAXI_PATH = os.path.expanduser('~/.taxi')
    AUTO_ADD_OPTIONS = {
            'NO': 'no',
            'TOP': 'top',
            'BOTTOM': 'bottom',
            'AUTO': 'auto'
    }

    DEFAULTS = {
            'auto_fill_days': '',
            'date_format': '%d/%m/%Y',
    }

    def __init__(self):
        self.config = None
        self.filepath = None

    def load(self, file):
        self.config = ConfigParser.RawConfigParser()
        self.filepath = file

        try:
            with open(self.filepath, 'r') as fp:
                self.config.readfp(fp)
        except IOError:
            raise IOError('The specified configuration file `%s` doesn\'t exist' % file)

    def get(self, section, key):
        try:
            return self.config.get(section, key)
        except ConfigParser.NoOptionError:
            if self.DEFAULTS.has_key(key):
                return self.DEFAULTS[key]

            raise

    def get_auto_fill_days(self):
        auto_fill_days = self.get('default', 'auto_fill_days')

        if not auto_fill_days:
            return []

        return [int(e.strip()) for e in auto_fill_days.split(',')]

    def get_projects(self):
        projects_cache = getattr(self, '_projects_cache', None)
        if projects_cache is not None:
            return projects_cache

        config_projects = self.config.items('wrmap')
        projects = {}

        for (project_name, id) in config_projects:
            parts = id.split('/', 1)

            if len(parts) == 2:
                value = (int(parts[0]), int(parts[1]))
            else:
                value = (int(parts[0]), None)

            projects[project_name] = value

        setattr(self, '_projects_cache', projects)

        return projects

    def get_reversed_projects(self):
        reversed_projects_cache = getattr(self, '_reversed_projects_cache', None)
        if reversed_projects_cache is not None:
            return reversed_projects_cache

        config_projects = self.config.items('wrmap')
        projects = {}

        for (project_name, id) in config_projects:
            parts = id.split('/', 1)

            if len(parts) == 2:
                value = (int(parts[0]), int(parts[1]))
            else:
                value = (int(parts[0]), None)

            projects[value] = project_name

        setattr(self, '_reversed_projects_cache', projects)

        return projects

    def project_exists(self, project_name):
        return project_name[-1] == '?' or project_name in self.get_projects()

    def get_close_matches(self, project_name):
        return difflib.get_close_matches(project_name, self.get_projects().keys(),
                                         cutoff=0.2)

    def add_activity(self, alias, projectid, activityid):
        if self.config is None:
            raise Exception('Trying to add an activity before loading the settings file')

        self.config.set('wrmap', alias, '%s/%s' % (projectid, activityid))
        self.write_config()

    def remove_activities(self, aliases):
        if self.config is None:
            raise Exception('Trying to add an activity before loading the settings file')

        for alias in aliases:
            self.config.remove_option('wrmap', alias)

        self.write_config()

    def write_config(self):
        with open(self.filepath, 'w') as file:
            self.config.write(file)

    def activity_exists(self, activity_name):
        return self.config.has_option('wrmap', activity_name)

settings = Settings()
