from __future__ import unicode_literals

import codecs
import os
import six
import shutil
import tempfile
from unittest import TestCase

from click.testing import CliRunner

from taxi.utils.file import expand_filename
from taxi.commands.base import cli


class CommandTestCase(TestCase):
    def setUp(self):
        _, self.config_file = tempfile.mkstemp()
        _, self.entries_file = tempfile.mkstemp()
        self.taxi_dir = tempfile.mkdtemp()

        with open(os.path.join(self.taxi_dir, 'projects.db'), 'w') as f:
            f.close()

        self.default_config = {
            'default': {
                'site': 'https://zebra.liip.ch',
                'username': 'john.doe',
                'password': 'john.doe',
                'date_format': '%d/%m/%Y',
                'editor': '/bin/true',
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

    def tearDown(self):
        entries_file = expand_filename(self.entries_file)

        os.remove(self.config_file)
        if os.path.exists(entries_file):
            os.remove(entries_file)
        shutil.rmtree(self.taxi_dir)

    def write_config(self, config):
        with open(self.config_file, 'w') as f:
            for (section, params) in six.iteritems(config):
                f.write("[%s]\n" % section)

                for (param, value) in six.iteritems(params):
                    f.write("%s = %s\n" % (param, value))

    def write_entries(self, contents):
        with codecs.open(expand_filename(self.entries_file), 'a', 'utf-8') as f:
            f.write(contents)

    def read_entries(self):
        with codecs.open(expand_filename(self.entries_file), 'r', 'utf-8') as f:
            contents = f.read()

        return contents

    def run_command(self, command_name, args=None, config_options=None):
        """
        Run the given taxi command with the given arguments and options. Before
        running the command, the configuration file is written with the given
        `config_options`, if any, or with the default config options.

        The output of the command is returned as a string.

        Args:
            command_name -- The name of the command to run
            args -- An optional list of arguments for the command
            config_options -- An optional options hash that will be used to
                              write the config file before running the command
        """
        if args is None:
            args = []

        if config_options is None:
            config_options = self.default_config
        else:
            config_options = dict(
                list(self.default_config.items()) +
                list(config_options.items())
            )
        self.write_config(config_options)

        args.insert(0, command_name)
        args.insert(0, '--taxi-dir=%s' % self.taxi_dir)
        args.insert(0, '--config=%s' % self.config_file)

        runner = CliRunner()
        result = runner.invoke(cli, args)

        return result.output
