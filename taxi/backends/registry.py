import pkg_resources
import urlparse


class BackendRegistry(object):
    def __init__(self):
        self._entry_points = {}
        self._backends_registry = {}
        self._backends_loaded = False

        for backend in pkg_resources.iter_entry_points('taxi.backends'):
            self._entry_points[backend.name] = backend

    def __getitem__(self, key):
        return self._backends_registry[key]

    def __setitem__(self, key, value):
        self._backends_registry[key] = value

    def __iter__(self):
        return iter(self._backends_registry)

    def __delitem__(self, key):
        self._backends_registry.__delitem__(key)

    def __contains__(self, key):
        self.load_backends()

        return key in self._backends_registry

    def items(self):
        return self._backends_registry.items()

    def populate(self, backends):
        for name, uri in backends.items():
            self._backends_registry[name] = self.load_backend(uri)

    def load_backend(self, backend_uri):
        parsed = urlparse.urlparse(backend_uri)
        options = dict(urlparse.parse_qsl(parsed.query))
        backend = self._entry_points[parsed.scheme].load()

        return backend(
            username=parsed.username, password=parsed.password,
            hostname=parsed.hostname, port=parsed.port,
            path=parsed.path, options=options
        )

backends_registry = BackendRegistry()
