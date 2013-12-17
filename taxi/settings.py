# -*- coding: utf-8 -*-
import ConfigParser
import os
import difflib

class Settings:
    TAXI_PATH = os.path.expanduser('~/.taxi')
    AUTO_ADD_OPTIONS = {
            'NO': 'no',
            'TOP': 'top',
            'BOTTOM': 'bottom',
            'AUTO': 'auto'
    }

    DEFAULTS = {
            'auto_fill_days': '',
            'date_format': '%d/%m/%Y',
            'auto_add': 'auto',
    }

    def __init__(self, file):
        self.config = ConfigParser.RawConfigParser()
        self.filepath = os.path.expanduser(file)

        try:
            with open(self.filepath, 'r') as fp:
                self.config.readfp(fp)
        except IOError:
            raise IOError('The specified configuration file `%s` doesn\'t exist' % file)

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

    def get_aliases(self, include_shared=True):
        aliases = {}
        config_aliases = self.config.items('wrmap')
        shared_config_aliases = (self.config.items('shared_wrmap')
                                 if self.config.has_section('shared_wrmap')
                                 else {})
        aliases_sections = [config_aliases]

        if include_shared:
            aliases_sections.insert(0, shared_config_aliases)

        for aliases_group in aliases_sections:
            for (alias, mapping) in aliases_group:
                (project_id, activity_id) = mapping.split('/', 1)
                aliases[alias] = (int(project_id), int(activity_id))

        return aliases

    def get_reversed_aliases(self, include_shared=True):
        aliases = self.get_aliases(include_shared)

        return dict((v, k) for k, v in aliases.iteritems())

    def search_aliases(self, mapping):
        aliases = []

        for (user_alias, mapped_alias) in self.get_aliases().iteritems():
            if (mapped_alias[0] != mapping[0] or
                    (mapping[1] is not None and mapped_alias[1] != mapping[1])):
                continue

            aliases.append((user_alias, mapped_alias))

        return aliases

    def search_mappings(self, search_alias):
        aliases = []

        for (user_alias, mapped_alias) in self.get_aliases().iteritems():
            if search_alias is None or user_alias.startswith(search_alias):
                aliases.append((user_alias, mapped_alias))

        return aliases

    def get_close_matches(self, project_name):
        return difflib.get_close_matches(project_name, self.get_aliases().keys(),
                                         cutoff=0.2)

    def add_alias(self, alias, projectid, activityid):
        self.config.set('wrmap', alias, '%s/%s' % (projectid, activityid))

    def remove_aliases(self, aliases):
        for alias in aliases:
            self.config.remove_option('wrmap', alias)

    def write_config(self):
        with open(self.filepath, 'w') as file:
            self.config.write(file)

    def activity_exists(self, activity_name):
        return self.config.has_option('wrmap', activity_name)

    def add_shared_alias(self, alias, project_id, activity_id):
        if not self.config.has_section('shared_wrmap'):
            self.config.add_section('shared_wrmap')

        self.config.set('shared_wrmap', alias,
                        '%s/%s' % (project_id, activity_id))
