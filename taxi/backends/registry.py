from __future__ import unicode_literals

import pkg_resources
from six.moves.urllib import parse

from ..exceptions import TaxiException


class BackendRegistry(object):
    """
    The backend registry holds information about available backends (registered
    via entry points) and their configuration. It is also responsible to load
    the backends and provides a way to easily get backends via a dict-like
    interface.

    The backend registry should be initialized via :py:meth:`populate`. The
    list of available backends is automatically discovered by checking the
    `taxi.backends` entry points.

    Once populated, backends can be loaded and retrieved with the following
    syntax:

        backends_registry['backend_name']
    """
    def __init__(self):
        self._entry_points = {}
        self._backends_registry = {}

        # Load the entry points and index them to avoid iterating every time we
        # need a specific backend
        for backend in pkg_resources.iter_entry_points('taxi.backends'):
            self._entry_points[backend.name] = backend

    def __getitem__(self, key):
        """
        Return the backend with the given name.
        """
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
        """
        Iterate over the given backends list and instantiate every backend
        found. Can raise :py:exc:`BackendNotFoundException` if a backend
        could not be found in the registered entry points.

        The `backends` parameter should be a dict with backend names as keys
        and URIs as values. For details about the URIs or the way backends are
        loaded, see the :py:meth:`load_backend` method.
        """
        for name, uri in backends.items():
            self._backends_registry[name] = self.load_backend(uri)

    def load_backend(self, backend_uri):
        """
        Return the instantiated backend object identified by the given
        `backend_uri`.

        The entry point that is used to create the backend object is determined
        by the protocol part of the given URI.
        """
        parsed = parse.urlparse(backend_uri)
        options = dict(parse.parse_qsl(parsed.query))

        try:
            backend = self._entry_points[parsed.scheme].load()
        except KeyError:
            raise BackendNotFoundError(
                "The requested backend `%s` could not be found in the "
                "registered entry points. Perhaps you forgot to install the "
                "corresponding backend package?" % parsed.scheme
            )

        password = (parse.unquote(parsed.password)
                    if parsed.password
                    else parsed.password)

        return backend(
            username=parsed.username, password=password,
            hostname=parsed.hostname, port=parsed.port,
            path=parsed.path, options=options
        )


class BackendNotFoundError(TaxiException):
    pass

backends_registry = BackendRegistry()
