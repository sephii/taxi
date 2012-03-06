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
    DEFAULT_DATE_FORMAT = '%d/%m/%Y'

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
        return self.config.get(section, key)

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

    def get_default_date_format(self):
        try:
            return self.get('default', 'date_format')
        except ConfigParser.NoOptionError:
            return self.DEFAULT_DATE_FORMAT

    def project_exists(self, project_name):
        return project_name[-1] == '?' or project_name in self.projects

    def get_close_matches(self, project_name):
        return difflib.get_close_matches(project_name, self.projects.keys(),\
                cutoff=0.2)

    def add_activity(self, alias, projectid, activityid):
        if self.config is None:
            raise Exception('Trying to add an activity before loading the settings file')

        file = open(self.filepath, 'w')
        self.config.set('wrmap', alias, '%s/%s' % (projectid, activityid))
        self.config.write(file)

settings = Settings()
