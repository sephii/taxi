class DummyBackend(object):
    def __init__(self, login, password, host, port, path, options):
        pass

    def authenticate(self, login, password):
        pass

    def push_entry(self, entry):
        print(entry)

    def get_projects(self):
        return []
