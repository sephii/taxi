from collections import defaultdict
import configparser
import copy
import os

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
            'round_entries': IntegerSetting(default=15),
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
                self.config.read_file(fp)
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
        alias_section = get_alias_section_name(mapping.backend)

        if not self.config.has_section(alias_section):
            self.config.add_section(alias_section)

        self.config.set(alias_section, alias,
                        Project.tuple_to_str(mapping.mapping) if mapping.mapping else None)

    def remove_aliases(self, aliases):
        for alias, mapping in aliases:
            backend_section = get_alias_section_name(mapping.backend)
            if self.config.has_option(backend_section, alias):
                self.config.remove_option(backend_section, alias)

    def write_config(self):
        with open(self.filepath, 'w') as file:
            self.config.write(file)

    def get_aliases(self):
        backends = self.get_backends()
        aliases = defaultdict(dict)

        for backend, uri in backends:
            backend_aliases_section = get_alias_section_name(backend)

            if self.config.has_section(backend_aliases_section):
                for (alias, mapping) in self.config.items(backend_aliases_section):
                    mapping = Project.str_to_tuple(mapping) if mapping else None
                    mapping_obj = Mapping(mapping, backend)

                    aliases[alias] = mapping_obj

        return aliases

    def get_backends(self):
        return self.config.items('backends')

    def get_shared_aliases_sections(self):
        backends = self.get_backends()

        shared_aliases_sections = [
            "{}_shared_aliases".format(backend) for backend, uri in backends
        ]

        return [
            section
            for section in shared_aliases_sections
            if self.config.has_section(section)
        ]

    def convert_to_6(self):
        for section in self.get_shared_aliases_sections():
            self.config.remove_section(section)

    @property
    def needed_conversions(self):
        shared_aliases_sections = self.get_shared_aliases_sections()
        conversions = [self.convert_to_6] if shared_aliases_sections else []

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


def get_alias_section_name(backend_name):
    return '%s_aliases' % backend_name
