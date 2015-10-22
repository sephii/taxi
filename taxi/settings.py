# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
import os

from six.moves import configparser

from .aliases import Mapping
from .projects import Project
from .utils.file import expand_date as file_expand_date


class Settings(dict):
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
        'file': '~/zebra/%Y/%m/%d.tks'
    }

    def __init__(self, file):
        self.config = configparser.RawConfigParser()
        self.filepath = os.path.expanduser(file)
        self._backends_registry = {}

        try:
            with open(self.filepath, 'r') as fp:
                self.config.readfp(fp)
        except IOError:
            raise IOError(
                "The specified configuration file `%s` doesn't exist" % file
            )

    def get(self, key, section='default', default_value=None):
        try:
            return self.config.get(section, key)
        except configparser.NoOptionError:
            if default_value is not None:
                return default_value

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

    def add_alias(self, alias, mapping):
        alias_section = get_alias_section_name(mapping.backend, False)

        if not self.config.has_section(alias_section):
            self.config.add_section(alias_section)

        self.config.set(alias_section, alias,
                        Project.tuple_to_str(mapping.mapping))

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

    def convert_to_4(self):
        """
        Convert a pre-4.0 configuration file to a 4.0 configuration file.
        """
        from six.moves.urllib import parse

        if not self.config.has_section('backends'):
            self.config.add_section('backends')

        site = parse.urlparse(self.get('site', default_value=''))
        backend_uri = 'zebra://{username}:{password}@{hostname}'.format(
            username=self.get('username', default_value=''),
            password=parse.quote(self.get('password', default_value=''),
                                 safe=''),
            hostname=site.hostname
        )
        self.config.set('backends', 'default', backend_uri)

        self.config.remove_option('default', 'username')
        self.config.remove_option('default', 'password')
        self.config.remove_option('default', 'site')

        if not self.config.has_section('default_aliases'):
            self.config.add_section('default_aliases')

        if not self.config.has_section('default_shared_aliases'):
            self.config.add_section('default_shared_aliases')

        if self.config.has_section('wrmap'):
            for alias, mapping in self.config.items('wrmap'):
                self.config.set('default_aliases', alias, mapping)

            self.config.remove_section('wrmap')

        if self.config.has_section('shared_wrmap'):
            for alias, mapping in self.config.items('shared_wrmap'):
                self.config.set('default_shared_aliases', alias, mapping)

            self.config.remove_section('shared_wrmap')

    def get_entries_file_path(self, expand_date=True):
        file_path = os.path.expanduser(self.get('file'))

        if expand_date:
            file_path = file_expand_date(file_path)

        return file_path


def get_alias_section_name(backend_name, shared_section=False):
    return '%s_%s' % (backend_name,
                      'aliases' if not shared_section else 'shared_aliases')
