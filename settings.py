import ConfigParser

class Settings:
    def load(self, file):
        config = ConfigParser.RawConfigParser()
        config.read(file)

    def get(self, section, key):
        return config.get(section, key)
