import pkg_resources
from urllib import parse

from .exceptions import TaxiException


class PluginsRegistry(object):
    """
    The plugins registry holds information about available plugins (registered
    via entry points) and their configuration. It is also responsible to load
    the backends and provides a way to easily get backends via a dict-like
    interface.

    The plugins registry should be initialized via :meth:`populate`. The list
    of available plugins is automatically discovered by checking the
    ``taxi.backends`` and ``taxi.commands`` entry points.

    Once populated, backend objects can be loaded and retrieved using the :meth:`get_backend` method::

        my_backend = plugins_registry.get_backend('backend_name')

        # Fetch the projects list from the loaded backend
        my_backend.get_projects()
    """
    BACKENDS_ENTRY_POINT = 'taxi.backends'
    COMMANDS_ENTRY_POINT = 'taxi.commands'
    ENTRY_POINTS = (BACKENDS_ENTRY_POINT, COMMANDS_ENTRY_POINT)

    def __init__(self):
        self._entry_points = {}
        self._backends_registry = {}

        # Load the entry points and index them to avoid iterating every time we
        # need a specific plugin
        for entry_point_type in self.ENTRY_POINTS:
            self._entry_points[entry_point_type] = {}

            for entry_point in pkg_resources.iter_entry_points(entry_point_type):
                self._entry_points[entry_point_type][entry_point.name] = entry_point

    def get_plugins(self):
        plugins_list = {}

        for entry_point_type, entry_points in self._entry_points.items():
            for entry_point in entry_points.values():
                plugin_name = entry_point.dist.project_name[5:]
                plugin_version = entry_point.dist.version

                if plugin_name:
                    plugins_list[plugin_name] = plugin_version

        return plugins_list

    def get_available_backends(self):
        """
        Return the names of the available backends.
        """
        return self._entry_points[self.BACKENDS_ENTRY_POINT].keys()

    def get_backend(self, key):
        """
        Return the backend instance for the backend with the given name.
        """
        return self._backends_registry[key]

    def get_backends_by_class(self, backend_class):
        """
        Return a list of backends that are instances of the given `backend_class`.
        """
        return [backend for backend in self._backends_registry.values() if isinstance(backend, backend_class)]

    def populate_backends(self, backends, context):
        """
        Iterate over the given backends list and instantiate every backend
        found. Can raise :exc:`BackendNotFoundError` if a backend
        could not be found in the registered entry points.

        The `backends` parameter should be a dict with backend names as keys
        and URIs as values.
        """
        for name, uri in backends.items():
            self._backends_registry[name] = self._load_backend(uri, context)

    def _load_backend(self, backend_uri, context):
        """
        Return the instantiated backend object identified by the given
        `backend_uri`.

        The entry point that is used to create the backend object is determined
        by the protocol part of the given URI.
        """
        parsed = parse.urlparse(backend_uri)
        options = dict(parse.parse_qsl(parsed.query))

        try:
            backend = self._entry_points[self.BACKENDS_ENTRY_POINT][parsed.scheme].load()
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
            path=parsed.path, options=options, context=context,
        )

    def register_commands(self):
        """
        Load entry points for custom commands.
        """
        for command in self._entry_points[self.COMMANDS_ENTRY_POINT].values():
            command.load()


class BackendNotFoundError(TaxiException):
    pass


plugins_registry = PluginsRegistry()
