# -*- coding: utf-8 -*-
from collections import defaultdict
import ConfigParser
import os
import difflib
import urlparse

from .backends import backends_registry
from .alias import Mapping
from .projects import Project


class Settings(dict):
    TAXI_PATH = os.path.expanduser('~/.taxi')
    AUTO_ADD_OPTIONS = {
        'NO': 'no',
        'TOP': 'top',
        'BOTTOM': 'bottom',
        'AUTO': 'auto'
    }

    DEFAULTS = {
        'auto_fill_days': '0,1,2,3,4',
        'date_format': '%d/%m/%Y',
        'auto_add': 'auto',
        'nb_previous_files': '1',
        'use_colors': '1',
        'local_aliases': '',
    }

    def __init__(self, file):
        self.config = ConfigParser.RawConfigParser()
        self.filepath = os.path.expanduser(file)
        self._backends_registry = {}

        try:
            with open(self.filepath, 'r') as fp:
                self.config.readfp(fp)
        except IOError:
            raise IOError(
                "The specified configuration file `%s` doesn't exist" % file
            )

    def get(self, key, section='default'):
        try:
            return self.config.get(section, key)
        except ConfigParser.NoOptionError:
            if key in self.DEFAULTS:
                return self.DEFAULTS[key]

            raise

    def get_auto_fill_days(self):
        auto_fill_days = self.get('auto_fill_days')

        if not auto_fill_days:
            return []

        return [int(e.strip()) for e in auto_fill_days.split(',')]

    def get_local_aliases(self):
        return [alias.strip()
                for alias in self.get('local_aliases').split(',')
                if alias.strip()]

    def get_close_matches(self, project_name):
        return difflib.get_close_matches(project_name,
                                         self.get_aliases().keys(), cutoff=0.2)

    def add_alias(self, alias, mapping):
        self.config.set('%s_aliases' % mapping.backend, alias,
                        '%s/%s' % mapping.mapping)

    def remove_aliases(self, aliases):
        for alias, mapping in aliases:
            for shared_section in [False, True]:
                backend_section = get_alias_section_name(mapping.backend,
                                                         shared_section)
                if self.config.has_option(backend_section, alias):
                    self.config.remove_option(backend_section, alias)
                    break

    def write_config(self):
        with open(self.filepath, 'w') as file:
            self.config.write(file)

    def add_shared_alias(self, alias, mapping):
        section = get_alias_section_name(mapping.backend, True)
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, alias, '%s/%s' % mapping.mapping)

    def clear_shared_aliases(self, backend):
        self.config.remove_section(get_alias_section_name(backend, True))
        self.config.add_section(get_alias_section_name(backend, True))

    def get_aliases(self):
        backends = self.get_backends()
        aliases = defaultdict(dict)

        for (backend, uri) in backends:
            for shared_section in [False, True]:
                backend_aliases_section = get_alias_section_name(
                    backend, shared_section
                )

                if self.config.has_section(backend_aliases_section):
                    for (alias, mapping) in self.config.items(backend_aliases_section):
                        mapping = Project.str_to_tuple(mapping)
                        mapping_obj = Mapping(mapping, backend)
                        aliases[alias] = mapping_obj

        return aliases

    def get_backends(self):
        return self.config.items('backends')


def get_alias_section_name(backend_name, shared_section=False):
    return '%s_%s' % (backend_name,
                      'aliases' if not shared_section else 'shared_aliases')
