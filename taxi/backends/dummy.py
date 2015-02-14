class DummyBackend(object):
    def __init__(self, login, password, host, port, path, options):
        pass

    def authenticate(self):
        pass

    def push_entry(self, date, entry):
        print(entry)

    def get_projects(self):
        return []
