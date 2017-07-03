# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
import copy
import os

from six.moves import configparser

from .aliases import Mapping
from .projects import Project
from .utils.file import expand_date as file_expand_date


class StringSetting(object):
    def __init__(self, default='', choices=None):
        if default and choices and default not in choices:
            raise ValueError(
                "Default value %s not in acceptable choices (%s)" %
                (default, choices)
            )

        self.default = default
        self.choices = choices

    def to_python(self, value):
        return value

    @property
    def value(self):
        if not hasattr(self, '_value'):
            return self.default

        return self._value

    @value.setter
    def value(self, value):
        value = self.to_python(value)

        if self.choices and value not in self.choices:
            raise ValueError("%s not an acceptable choice")

        self._value = value


class ListSetting(StringSetting):
    def to_python(self, value):
        value = super(ListSetting, self).to_python(value)
        return list(filter(None, map(lambda x: x.strip(), value.split(','))))


class IntegerSetting(StringSetting):
    def to_python(self, value):
        value = super(IntegerSetting, self).to_python(value)
        return int(value)


class IntegerListSetting(ListSetting):
    def to_python(self, value):
        return list(map(int, super(IntegerListSetting, self).to_python(value)))


class BooleanSetting(StringSetting):
    VALUES_MAPPING = {
        True: ['1', 'true'],
        False: ['0', 'false']
    }

    def to_python(self, value):
        if value not in self.VALUES_MAPPING[True] + self.VALUES_MAPPING[False]:
            raise ValueError(
                "Value %s is not accepted for this setting." % value
            )

        return value.lower() in self.VALUES_MAPPING[True]


class Settings(object):
    AUTO_ADD_OPTIONS = {
        'NO': 'no',
        'TOP': 'top',
        'BOTTOM': 'bottom',
        'AUTO': 'auto'
    }

    SETTINGS = {
        'taxi': {
            'auto_fill_days': IntegerListSetting(default=range(0, 5)),
            'date_format': StringSetting(default='%d/%m/%Y'),
            'auto_add': StringSetting(default='auto',
                                      choices=AUTO_ADD_OPTIONS.values()),
            'nb_previous_files': IntegerSetting(default=1),
            'file': StringSetting(default='~/zebra/%Y/%m/%d.tks'),
            'editor': StringSetting(),
            'regroup_entries': BooleanSetting(default=True),
        },
        'flags': {
            'ignored': StringSetting(default='?'),
            'pushed': StringSetting(default='='),
        }
    }

    def __init__(self, file):
        self.config = configparser.RawConfigParser(allow_no_value=True)
        self.filepath = os.path.expanduser(file)
        self._settings = {}

        try:
            with open(self.filepath, 'r') as fp:
                self.config.readfp(fp)
        except IOError:
            raise IOError(
                "The specified configuration file `%s` doesn't exist" % file
            )

        # Copy the class settings to the instance so we don't set global values
        # on the class
        for section, settings in self.SETTINGS.items():
            self._settings[section] = {}
            for key, setting in settings.items():
                self._settings[section][key] = copy.copy(setting)

                try:
                    value = self.config.get(section, key)
                    self._settings[section][key].value = value
                except ValueError:
                    raise ValueError(
                        "Value %s is not allowed for setting %s:%s" %
                        (value, section, key)
                    )
                except (configparser.NoOptionError, configparser.NoSectionError):
                    pass

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, section='taxi'):
        return self._settings[section][key].value

    def add_alias(self, alias, mapping):
        alias_section = get_alias_section_name(mapping.backend, False)

        if not self.config.has_section(alias_section):
            self.config.add_section(alias_section)

        self.config.set(alias_section, alias,
                        Project.tuple_to_str(mapping.mapping) if mapping.mapping else None)

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
                        mapping = Project.str_to_tuple(mapping) if mapping is not None else None
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

    def convert_to_4_1(self):
        if not self.config.has_option('default', 'local_aliases'):
            return

        local_aliases = self.config.get('default', 'local_aliases')
        local_aliases = ListSetting().to_python(local_aliases)

        if not self.config.has_section('backends'):
            self.config.add_section('backends')

        self.config.set('backends', 'local', 'dummy://')

        if not self.config.has_section('local_aliases'):
            self.config.add_section('local_aliases')

        for alias in local_aliases:
            self.config.set('local_aliases', alias, None)

        self.config.remove_option('default', 'local_aliases')

    def convert_to_4_3(self):
        if not self.config.has_section('default'):
            return

        defaults = self.config.items('default')

        try:
            self.config.add_section('taxi')
        except configparser.DuplicateSectionError:
            pass

        for key, value in defaults:
            self.config.set('taxi', key, value)

        self.config.remove_section('default')

    @property
    def needed_conversions(self):
        conversions = []

        if self.config.has_option('default', 'local_aliases'):
            conversions.append(self.convert_to_4_1)

        if self.config.has_section('default'):
            conversions.append(self.convert_to_4_3)

        return conversions

    def get_entries_file_path(self, expand_date=True):
        file_path = os.path.expanduser(self.get('file'))

        if expand_date:
            file_path = file_expand_date(file_path)

        return file_path

    def get_flags(self):
        return {flag: value.value for flag, value in self._settings['flags'].items()}

    def get_add_to_bottom(self):
        return {'auto': None, 'bottom': True, 'top': False}.get(self.get('auto_add'), None)


def get_alias_section_name(backend_name, shared_section=False):
    return '%s_%s' % (backend_name,
                      'aliases' if not shared_section else 'shared_aliases')
