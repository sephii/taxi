import pkg_resources


class BackendRegistry(object):
    def __init__(self):
        self._backends_registry = {}
        self._backends_loaded = False

    def __getitem__(self, key):
        self.load_backends()

        return self._backends_registry[key]

    def __setitem__(self, key, value):
        self._backends_registry[key] = value

    def __iter__(self):
        self.load_backends()

        return iter(self._backends_registry)

    def __delitem__(self, key):
        self.load_backends()
        self._backends_registry.__delitem__(key)

    def __contains__(self, key):
        self.load_backends()

        return key in self._backends_registry

    def items(self):
        return self._backends_registry.items()

    def load_backends(self):
        if self._backends_loaded:
            return

        for backend in pkg_resources.iter_entry_points('taxi.backends'):
            self._backends_registry[backend.name] = backend.load()

backends_registry = BackendRegistry()
