import collections
import difflib


class Mapping(collections.namedtuple('BaseMapping', ['mapping', 'backend'])):
    def is_mapped(self):
        """
        Return False if the alias doesn't have any mapping, ie. the alias is
        declared but without any mapping information. Return True otherwise.
        """
        return self.mapping is not None


class AliasesDatabase(object):
    """
    Dict-like object containing aliases and their corresponding mappings.

    Example usage:

        >>> aliases_database = AliasDatabase()
        >>> aliases_database['my_alias'] = Mapping(mapping=(1, 2),
        backend='dummy')
        >>> 'my_alias' in aliases_database
        True
    """
    def __init__(self, aliases=None):
        """
        Create an empty alias database and optionally populate it with the
        given `aliases`. If `aliases` is given, it must be a dictionary
        containing :py:class:`Mapping` objects.
        """
        self.reset()

        if aliases:
            self.aliases = aliases

    def __getitem__(self, key):
        """
        Return the corresponding :py:class:`Mapping` object. It might raise
        KeyError if not found but that's the expected behaviour.
        """
        return self.aliases[key]

    def __setitem__(self, key, value):
        self.aliases[key] = value

    def __contains__(self, key):
        return key in self.aliases

    def __iter__(self):
        """
        Iterate over aliases.
        """
        return self.aliases.__iter__()

    def iteritems(self):
        """
        Python 2 compatibility.
        """
        return self.items()

    def items(self):
        return self.aliases.items()

    def keys(self):
        return list(self.aliases.keys())

    def update(self, other):
        self.aliases.update(other)

    def reset(self):
        """
        Reset the aliases to an empty state.
        """
        self.aliases = {}

    def get_reversed_aliases(self):
        """
        Return the reversed aliases dict. Instead of being in the form
        {'alias': mapping}, the dict is in the form {mapping: 'alias'}.
        """
        return dict((v, k) for k, v in self.aliases.items())

    def get_close_matches(self, alias):
        """
        Return the aliases that look like the given alias.
        """
        return difflib.get_close_matches(alias,
                                         self.keys(), cutoff=0.2)

    def filter_from_mapping(self, mapping, backend=None):
        """
        Return mappings that either exactly correspond to the given `mapping`
        tuple, or, if the second item of `mapping` is `None`, include mappings
        that only match the first item of `mapping` (useful to show all
        mappings for a given project).
        """
        def mapping_filter(key_item):
            key, item = key_item

            return (
                (mapping is None or item.mapping == mapping or
                    (mapping[1] is None and item.mapping is not None and item.mapping[0] == mapping[0])) and
                (backend is None or item.backend == backend)
            )

        items = [item for item in self.items() if mapping_filter(item)]

        aliases = collections.OrderedDict(
            sorted(items, key=lambda alias: alias[1].mapping
                   if alias[1] is not None else (0, 0))
        )

        return aliases

    def filter_from_alias(self, alias, backend=None):
        """
        Return aliases that start with the given `alias`, optionally filtered
        by backend.
        """
        def alias_filter(key_item):
            key, item = key_item

            return ((alias is None or alias in key) and
                    (backend is None or item.backend == backend))

        items = filter(alias_filter, self.items())

        aliases = collections.OrderedDict(sorted(items, key=lambda a: a[0].lower()))

        return aliases

aliases_database = AliasesDatabase()
