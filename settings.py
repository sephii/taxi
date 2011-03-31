import ConfigParser

class Settings:
    def load(self, file):
        self.config = ConfigParser.RawConfigParser()
        self.config.read(file)

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

settings = Settings()
