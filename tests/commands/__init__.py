from contextlib import contextmanager
import tempfile
from unittest import TestCase

from mock import Mock

from taxi.remote import ZebraRemote


class CommandTest(TestCase):
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

    def setUp(self):
        def zebra_remote_send_entries(entries, callback):
            pushed_entries = [
                item for sublist in entries.values() for item in sublist
            ]

            return (pushed_entries, [])

        self.original_zebra_remote_send_entries = ZebraRemote.send_entries
        ZebraRemote.send_entries = Mock(side_effect=zebra_remote_send_entries)

    def tearDown(self):
        ZebraRemote.send_entries = self.original_zebra_remote_send_entries

    @contextmanager
    def generate_config_file(self, config):
        with tempfile.NamedTemporaryFile() as f:
            for (section, params) in config.iteritems():
                f.write("[%s]\n" % section)

                for (param, value) in params.iteritems():
                    f.write("%s = %s\n" % (param, value))

            f.flush()
            yield f

    @contextmanager
    def generate_entries_file(self, contents):
        with tempfile.NamedTemporaryFile() as f:
            f.write(contents)
            f.flush()

            yield f
