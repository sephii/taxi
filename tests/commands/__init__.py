import os
from StringIO import StringIO
import tempfile
from unittest import TestCase

from mock import Mock

from taxi.remote import ZebraRemote


class CommandTestCase(TestCase):
    default_config = {
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

    default_options = {
    }

    def setUp(self):
        def zebra_remote_send_entries(entries, callback):
            pushed_entries = [
                item for sublist in entries.values() for item in sublist
            ]

            return (pushed_entries, [])

        self.original_zebra_remote_send_entries = ZebraRemote.send_entries
        ZebraRemote.send_entries = Mock(side_effect=zebra_remote_send_entries)

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
