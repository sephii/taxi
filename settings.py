import ConfigParser

class Settings:
    def load(self, file):
        self.config = ConfigParser.RawConfigParser()
        self.config.read(file)

    def get(self, section, key):
        return self.config.get(section, key)
