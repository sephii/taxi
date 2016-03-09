from __future__ import unicode_literals

import codecs
import collections
import copy
from functools import wraps
import os
import re
import six
import shutil
import tempfile
from unittest import TestCase

from click.testing import CliRunner

from taxi.backends import BaseBackend, PushEntryFailed, PushEntriesFailed
from taxi.backends.registry import backends_registry
from taxi.commands.base import cli
from taxi.projects import ProjectsDb
from taxi.utils.file import expand_date


class TestBackendEntryPoint(object):
    """
    Dedicated backend for tests. Entries with the alias `fail` will fail when
    trying to push them.
    """
    class TestBackend(BaseBackend):
        def __init__(self, *args, **kwargs):
            super(TestBackendEntryPoint.TestBackend, self).__init__(
                *args, **kwargs
            )
            self.entries = []

        def push_entry(self, date, entry):
            self.entries.append(entry)

            if entry.alias == 'fail':
                raise PushEntryFailed()

        def post_push_entries(self):
            failed_entries = {}

            for entry in self.entries:
                if entry.alias == 'post_push_fail':
                    failed_entries[entry] = 'foobar'

            if failed_entries:
                raise PushEntriesFailed(entries=failed_entries)

    def load(self):
        return self.TestBackend


class CommandTestCase(TestCase):
    def setUp(self):
        _, self.config_file = tempfile.mkstemp()
        _, self.entries_file = tempfile.mkstemp()
        self.taxi_dir = tempfile.mkdtemp()
        # Keep the original entry points to restore them in tearDown
        self.backends_original_entry_points = backends_registry._entry_points

        # Hot swap the entry points from the backends registry with our own
        # test backend. This avoids having to register the test backend in the
        # setup.py file
        backends_registry._entry_points = {
            'test': TestBackendEntryPoint(),
            'dummy': TestBackendEntryPoint(),
        }

        # Create an empty projects db file
        projects_db_file = os.path.join(self.taxi_dir,
                                        ProjectsDb.PROJECTS_FILE)
        with open(projects_db_file, 'w') as f:
            f.close()

        existing_settings = (self._settings
                             if hasattr(self, '_settings')
                             else {})
        self._settings = recursive_update({
            'default': {
                'date_format': '%d/%m/%Y',
                'editor': '/bin/true',
                'file': self.entries_file,
                'use_colors': '0'
            },
            'backends': {
                'test': 'test:///',
                'local': 'dummy:///',
            },
            'test_aliases': {
                'alias_1': '123/456',
                'fail': '456/789',
                'post_push_fail': '456/789',
            },
        }, existing_settings)

    def tearDown(self):
        backends_registry._entry_points = self.backends_original_entry_points
        entries_file = expand_date(self.entries_file)

        os.remove(self.config_file)
        if os.path.exists(entries_file):
            os.remove(entries_file)
        shutil.rmtree(self.taxi_dir)

    def assertLineIn(self, line, content):
        """
        Check that the given line is present in the given content, ignoring
        whitespace differences.
        """
        def remove_spaces(text):
            chars_to_strip = [' ', '\t']

            for char in chars_to_strip:
                text = text.replace(char, '')

            return text

        self.assertIn(
            remove_spaces(line),
            remove_spaces(content),
            "Line `%s` not found in `%s`" % (line, content)
        )


    def settings(self, *args, **kwargs):
        """
        Context manager to temporarily override the settings:

            with self.settings({'default': {'file': '/tmp/test.txt'}}):
                ...
        """
        return override_settings(*args, container=self, **kwargs)

    def write_config(self, config):
        with open(self.config_file, 'w') as f:
            for (section, params) in six.iteritems(config):
                f.write("[%s]\n" % section)

                for (param, value) in six.iteritems(params):
                    f.write("%s = %s\n" % (param, value))

    def write_entries(self, contents):
        with codecs.open(expand_date(self.entries_file), 'a', 'utf-8') as f:
            f.write(contents)

    def read_entries(self):
        with codecs.open(expand_date(self.entries_file), 'r', 'utf-8') as f:
            contents = f.read()

        return contents

    def run_command(self, command_name, args=None, input=None):
        """
        Run the given taxi command with the given arguments and options. The
        output of the command is returned as a string.

        Args:
            command_name -- The name of the command to run
            args -- An optional list of arguments for the command
        """
        if args is None:
            args = []

        self.write_config(self._settings)

        args.insert(0, command_name)
        args.insert(0, '--taxi-dir=%s' % self.taxi_dir)
        args.insert(0, '--config=%s' % self.config_file)

        runner = CliRunner()
        result = runner.invoke(cli, args, input=input, standalone_mode=False)

        if result.exception:
            raise result.exception

        return result.output


class override_settings(object):
    """
    Allow to temporarily override settings in the given portion of code. Can be
    used as a class decorator, a method decorator or as a context manager.
    Example usage:

        @override_settings({'default': {'file': '/tmp/test'txt'}})
        class MyTestClass(CommandTestCase):
            ...
    """
    def __init__(self, settings=None, container=None):
        self.settings = settings or {}
        # The container is the test instance that holds the settings
        self.container = container

    def __call__(self, func):
        # Class decorator
        if isinstance(func, type):
            self.container = func
            self.enable()

            return func
        else:
            # Method decorator. This only works on bound methods since we use
            # the first arg as the settings container
            @wraps(func)
            def inner(*args, **kwargs):
                self.container = args[0]

                with self:
                    return func(*args, **kwargs)

            return inner

    def enable(self):
        # The _settings attribute might not exist, eg. if it's used as a class
        # decorator
        if not hasattr(self.container, '_settings'):
            self.container._settings = {}

        # Keep a copy of the current settings and override them
        self.original_settings = copy.deepcopy(self.container._settings)
        for section, settings in six.iteritems(self.settings):
            if section not in self.container._settings:
                self.container._settings[section] = {}

            for setting, value in six.iteritems(settings):
                self.container._settings[section][setting] = value

    def disable(self):
        self.container._settings = self.original_settings

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disable()


def recursive_update(d, u):
    """
    Recursive dict update.
    """
    for k, v in six.iteritems(u):
        if isinstance(v, collections.Mapping):
            r = recursive_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
