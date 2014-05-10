import os
from StringIO import StringIO
import tempfile
from unittest import TestCase

from mock import Mock

from taxi.app import Taxi
from taxi.remote import ZebraRemote


class CommandTestCase(TestCase):
    def setUp(self):
        def zebra_remote_send_entries(entries, callback):
            pushed_entries = [
                item for sublist in entries.values() for item in sublist
            ]

            return (pushed_entries, [])

        self.original_zebra_remote_send_entries = ZebraRemote.send_entries
        ZebraRemote.send_entries = Mock(side_effect=zebra_remote_send_entries)
        self.default_config = {
            'default': {
                'site': 'https://zebra.liip.ch',
                'username': 'john.doe',
                'password': 'john.doe',
                'date_format': '%d/%m/%Y',
            },
            'wrmap': {
                'alias_1': '123/456'
            }
        }

        self.default_options = {
        }

        self.stdout = StringIO()
        _, self.config_file = tempfile.mkstemp()
        _, self.entries_file = tempfile.mkstemp()
        self.default_options['config'] = self.config_file
        self.default_options['file'] = self.entries_file
        self.default_options['stdout'] = self.stdout

    def tearDown(self):
        ZebraRemote.send_entries = self.original_zebra_remote_send_entries

        os.remove(self.config_file)
        os.remove(self.entries_file)

    def write_config(self, config):
        with open(self.config_file, 'w') as f:
            for (section, params) in config.iteritems():
                f.write("[%s]\n" % section)

                for (param, value) in params.iteritems():
                    f.write("%s = %s\n" % (param, value))

    def write_entries(self, contents):
        with open(self.entries_file, 'w') as f:
            f.write(contents)

    def read_entries(self):
        with open(self.entries_file, 'r') as f:
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
