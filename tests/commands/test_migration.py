from __future__ import unicode_literals

from taxi.settings import Settings

from . import override_settings, CommandTestCase


class MigrationTestCase(CommandTestCase):
    @override_settings({'default': {'local_aliases': '_foo, _bar'}})
    def test_migration_to_41_copies_local_aliases(self):
        stdout = self.run_command('alias', ['list', '_foo'])
        self.assertIn('[local] _foo -> not mapped', stdout)

        settings = Settings(self.config_file)
        self.assertTrue(settings.config.has_section('local_aliases'))
        self.assertTrue(settings.config.has_option('local_aliases', '_foo'))
        self.assertIsNone(settings.config.get('local_aliases', '_foo'))
        self.assertTrue(settings.config.has_option('local_aliases', '_bar'))
        self.assertIsNone(settings.config.get('local_aliases', '_bar'))
