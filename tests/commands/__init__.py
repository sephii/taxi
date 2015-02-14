import os
from StringIO import StringIO
import tempfile
from unittest import TestCase

from mock import Mock

from taxi.app import Taxi
from taxi.remote import ZebraRemote
from taxi.utils.file import expand_filename


class CommandTestCase(TestCase):
    def setUp(self):
        def zebra_remote_send_entries(entries, mappings, callback):
            pushed_entries = []
            failed_entries = []

            for (_, date_entries) in entries.iteritems():
                for entry in date_entries:
                    pushed = entry.alias != 'fail'

                    if pushed:
                        pushed_entries.append(entry)
                    else:
                        failed_entries.append((entry, 'fail'))

                    callback(entry,
                             entry.description if not pushed else None)

            return (pushed_entries, failed_entries)

        self.original_zebra_remote_send_entries = ZebraRemote.send_entries
        ZebraRemote.send_entries = Mock(side_effect=zebra_remote_send_entries)
        self.stdout = StringIO()

        _, self.config_file = tempfile.mkstemp()
        _, self.entries_file = tempfile.mkstemp()
        _, self.projects_db = tempfile.mkstemp()

        self.default_config = {
            'default': {
                'site': 'https://zebra.liip.ch',
                'username': 'john.doe',
                'password': 'john.doe',
                'date_format': '%d/%m/%Y',
                'editor': '/bin/false',
                'file': self.entries_file,
                'use_colors': '0'
            },
            'backends': {
                'dummy': 'dummy://foo:bar@localhost/test?foo=bar',
            },
            'dummy_aliases': {
                'alias_1': '123/456'
            },
        }

        self.default_options = {
        }

        self.default_options['config'] = self.config_file
        self.default_options['stdout'] = self.stdout
        self.default_options['projects_db'] = self.projects_db

    def tearDown(self):
        ZebraRemote.send_entries = self.original_zebra_remote_send_entries

        entries_file = expand_filename(self.entries_file)

        os.remove(self.config_file)
        if os.path.exists(entries_file):
            os.remove(entries_file)
        os.remove(self.projects_db)

    def write_config(self, config):
        with open(self.config_file, 'w') as f:
            for (section, params) in config.iteritems():
                f.write("[%s]\n" % section)

                for (param, value) in params.iteritems():
                    f.write("%s = %s\n" % (param, value))

    def write_entries(self, contents):
        with open(expand_filename(self.entries_file), 'a') as f:
            f.write(contents)

    def read_entries(self):
        with open(expand_filename(self.entries_file), 'r') as f:
            contents = f.read()

        return contents

    def run_command(self, command_name, args=None, options=None,
                    config_options=None):
        """
        Run the given taxi command with the given arguments and options. Before
        running the command, the configuration file is written with the given
        `config_options`, if any, or with the default config options.

        The output of the command is put in the `self.stdout` property and
        returned as a string.

        Args:
            command_name -- The name of the command to run
            args -- An optional list of arguments for the command
            options -- An optional options hash for the command
            config_options -- An optional options hash that will be used to
                              write the config file before running the command
        """
        if args is None:
            args = []

        if options is None:
            options = self.default_options

        if config_options is None:
            config_options = self.default_config
        else:
            config_options = dict(
                self.default_config.items() + config_options.items()
            )
        self.write_config(config_options)

        self.stdout = StringIO()
        options['stdout'] = self.stdout

        app = Taxi()
        app.run_command(command_name, options=options, args=args)

        return self.stdout.getvalue()
