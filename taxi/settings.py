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
        parsed = self.config.read(self.filepath)

        if len(parsed) == 0:
            raise Exception('The specified configuration file `%s` doesn\'t exist' % file)

        self.get_projects()

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
        self.projects = {}
        projects = self.config.items('wrmap')

        for (project_name, id) in projects:
            parts = id.split('/', 1)

            if len(parts) == 2:
                value = (parts[0], parts[1])
            else:
                value = (parts[0], None)

            self.projects[project_name] = value

    def project_exists(self, project_name):
        return project_name[-1] == '?' or project_name in self.projects

    def get_close_matches(self, project_name):
        return difflib.get_close_matches(project_name, self.projects.keys(),\
                cutoff=0.2)

    def add_activity(self, alias, projectid, activityid):
        if self.config is None:
            raise Exception('Trying to add an activity before loading the settings file')

        file = codecs.open(self.filepath, 'w', 'utf-8')
        self.config.set('wrmap', alias, '%s/%s' % (projectid, activityid))
        self.config.write(file)

    def activity_exists(self, activity_name):
        return self.config.has_option('wrmap', activity_name)

settings = Settings()
