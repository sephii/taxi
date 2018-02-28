import os

import py
import pytest
from click.testing import CliRunner
from six.moves import configparser

from taxi.backends import BaseBackend, PushEntriesFailed, PushEntryFailed
from taxi.commands.base import cli as taxi_cli
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


class ConfigFile:
    DEFAULT_CONFIG = {
        'taxi': {
            'editor': '/bin/touch',
            'date_format': '%d/%m/%Y',
        },
        'backends': {
            'test': 'test:///',
            'local': 'dummy:///',
        },
        'test_aliases': {
            'alias_1': '123/456',
            'post_push_fail': '123/457',
            'fail': '123/458',
        }
    }

    def __init__(self, path):
        self.path = path
        self.config = configparser.RawConfigParser()
        self._sync = False

        for section, params in self.DEFAULT_CONFIG.items():
            for key, value in params.items():
                self.set(section, key, value)

        self.save()

        self._sync = True

    def set(self, section, attr, value):
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, attr, value)

        if self._sync:
            self.save()

    def set_dict(self, options):
        self.sync = False

        for section, items in options.items():
            for key, value in items.items():
                self.set(section, key, value)

        self.sync = True
        self.save()

    def clear_section(self, section):
        self.config.remove_section(section)
        self.config.add_section(section)

    def save(self):
        with open(self.path, 'w') as cf:
            self.config.write(cf)


class EntriesFileGenerator(py.path.local):
    def __init__(self, tmpdir, pattern):
        self.pattern = pattern
        self.tmpdir = tmpdir

    def patch_config(self, config):
        config.set('taxi', 'file', os.path.join(str(self.tmpdir), self.pattern))

    def expand(self, date):
        return self.tmpdir.join(expand_date(self.pattern, date))


@pytest.fixture
def config(tmpdir):
    config_file = ConfigFile(str(tmpdir.join('config.ini')))
    config_file.set('taxi', 'file', str(tmpdir.join('entries.tks')))

    return config_file


@pytest.fixture
def data_dir(tmpdir):
    return tmpdir.mkdir('data')


@pytest.fixture
def entries_file(tmpdir, config):
    new_entries_file = tmpdir.join('foo.tks')
    config.set('taxi', 'file', str(new_entries_file))

    return new_entries_file


@pytest.fixture
def cli(config, data_dir):
    def inner(cmd, args=None, input=None):
        if not args:
            args = []

        args.insert(0, cmd)
        args.insert(0, '--config=%s' % config.path)
        args.insert(0, '--taxi-dir=%s' % str(data_dir))

        runner = CliRunner()
        result = runner.invoke(
            taxi_cli, args, input=input, standalone_mode=False, catch_exceptions=False
        )

        return result.output

    return inner


@pytest.fixture(autouse=True)
def set_test_backends(monkeypatch):
    monkeypatch.setattr('taxi.plugins.plugins_registry._entry_points', {
        'taxi.backends': {
            'test': TestBackendEntryPoint(),
            'dummy': TestBackendEntryPoint(),
        }
    })
