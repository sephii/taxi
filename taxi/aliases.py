from __future__ import unicode_literals

import collections
import difflib
import itertools
import six


Mapping = collections.namedtuple('Mapping', ['mapping', 'backend'])


class AliasesDatabase(object):
    """
    Dict-like object containing aliases and their corresponding mappings. It
    contains aliases and "local aliases". Local aliases are not mapped to
    anything, so even if they're present in the database, they'll always have a
    `None` value.

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
        Return the corresponding :py:class:`Mapping` object or `None` if the
        alias is local.
        """
        if key in self.local_aliases:
            return None
        else:
            # Might raise KeyError if not found but that's the expected
            # behaviour
            return self.aliases[key]

    def __setitem__(self, key, value):
        self.aliases[key] = value

    def __contains__(self, key):
        return key in self.aliases or key in self.local_aliases

    def __iter__(self):
        """
        Iterate over local aliases and standard aliases. Local aliases always
        come first in the iteration.
        """
        return itertools.chain(self.local_aliases_to_dict(), self.aliases)

    def iteritems(self):
        """
        Python 2 compatibility.
        """
        return self.items()

    def items(self):
        return itertools.chain(
            six.iteritems(self.local_aliases_to_dict()),
            six.iteritems(self.aliases)
        )

    def keys(self):
        return list(self.aliases.keys()) + list(self.local_aliases)

    def update(self, other):
        self.aliases.update(other)

    def reset(self):
        """
        Reset both the aliases and local aliases to an empty state.
        """
        self.local_aliases = set()
        self.aliases = {}

    def local_aliases_to_dict(self):
        """
        Transform the local aliases set to a dict with null values.
        """
        return dict((alias, None) for alias in self.local_aliases)

    def is_local(self, alias):
        """
        Return `True` if the given alias is in the `local_aliases` set.
        """
        return alias in self.local_aliases

    def get_reversed_aliases(self):
        """
        Return the reversed aliases dict. Instead of being in the form
        {'alias': mapping}, the dict is in the form {mapping: 'alias'}. Local
        aliases are not included in this list for the obvious reason that
        they're all mapped to a `None` mapping.
        """
        return dict((v, k) for k, v in six.iteritems(self.aliases))

    def get_close_matches(self, alias):
        """
        Return the aliases that look like the given alias.
        """
        return difflib.get_close_matches(alias,
                                         self.keys(), cutoff=0.2)

    def filter_from_mapping(self, mapping):
        """
        Return mappings that either exactly correspond to the given `mapping`
        tuple, or, if the second item of `mapping` is `None`, include mappings
        that only match the first item of `mapping` (useful to show all
        mappings for a given project).
        """
        def mapping_filter(key_item):
            key, item = key_item

            return (
                item.mapping == mapping
                or (mapping[1] is None and item.mapping[0] == mapping[0])
            )

        if not mapping:
            items = six.iteritems(self)
        else:
            items = six.moves.filter(mapping_filter, six.iteritems(self))

        aliases = collections.OrderedDict(
            sorted(items, key=lambda alias: alias[1].mapping
                   if alias[1] is not None else (0, 0))
        )

        return aliases

    def filter_from_alias(self, alias):
        """
        Return aliases that start with the given `alias`.
        """
        def alias_filter(key_item):
            key, item = key_item
            return key.startswith(alias)

        if not alias:
            items = six.iteritems(self)
        else:
            items = six.moves.filter(alias_filter, six.iteritems(self))

        aliases = collections.OrderedDict(
            sorted(items, key=lambda alias: alias[1].mapping
                   if alias[1] is not None else (0, 0))
        )

        return aliases

aliases_database = AliasesDatabase()
