import abc


class BaseBackend(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, username, password, hostname, port, path, options):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.path = path
        self.options = options

    def authenticate(self):
        pass

    @abc.abstractmethod
    def push_entry(self, date, entry):
        pass

    def get_projects(self):
        return []

    def shutdown(self):
        pass


class PushEntryFailed(Exception):
    pass
