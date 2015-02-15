import collections
import itertools


Mapping = collections.namedtuple('Mapping', ['mapping', 'backend'])


class AliasDatabase(object):
    """
    TODO: comment
    """
    def __init__(self, aliases=None):
        self.reset()

        if aliases:
            self.aliases = aliases

    def __getitem__(self, key):
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
        return itertools.chain(self.local_aliases_to_dict(), self.aliases)

    def iteritems(self):
        """
        Python 2 compatibility.
        """
        return self.items()

    def items(self):
        return itertools.chain(
            self.local_aliases_to_dict().iteritems(),
            self.aliases.iteritems()
        )

    def keys(self):
        return self.aliases.keys() + list(self.local_aliases)

    def update(self, other):
        self.aliases.update(other)

    def reset(self):
        self.local_aliases = set()
        self.aliases = {}

    def local_aliases_to_dict(self):
        return dict((alias, None) for alias in self.local_aliases)

    def is_local(self, alias):
        return alias in self.local_aliases

    def get_reversed_aliases(self):
        return dict((v, k) for k, v in self.aliases.iteritems())

    def filter_from_mapping(self, mapping):
        def mapping_filter((key, item)):
            return (
                item.mapping == mapping
                or (mapping[1] is None and item.mapping[0] == mapping[0])
            )

        if not mapping:
            items = self.iteritems()
        else:
            items = itertools.ifilter(mapping_filter, self.iteritems())

        aliases = collections.OrderedDict(
            sorted(items, key=lambda alias: alias[1].mapping
                   if alias[1] is not None else '')
        )

        return aliases

    def filter_from_alias(self, alias):
        def alias_filter((key, item)):
            return key.startswith(alias)

        if not alias:
            items = self.iteritems()
        else:
            items = itertools.ifilter(alias_filter, self.iteritems())

        aliases = collections.OrderedDict(
            sorted(items, key=lambda alias: alias[1].mapping
                   if alias[1] is not None else '')
        )

        return aliases

alias_database = AliasDatabase()
