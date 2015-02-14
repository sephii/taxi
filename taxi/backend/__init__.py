import pkg_resources


class BackendRegistry(object):
    def __init__(self):
        self._backend_registry = {}

    def __getitem__(self, key):
        if key not in self._backend_registry:
            for backend in pkg_resources.iter_entry_points('taxi_backends'):
                if backend.name == key:
                    self._backend_registry[backend.name] = backend.load()
                    break

        return self._backend_registry[key]

    def __setitem__(self, key, value):
        self._backend_registry[key] = value

    def __iter__(self):
        return iter(self._backend_registry)

    def __delitem__(self, key):
        self._backend_registry.__delitem__(key)

    def __contains__(self, key):
        return key in self._backend_registry

backends = BackendRegistry()
