from . import CommandTestCase, override_settings


class UpdateCommandTestCase(CommandTestCase):
    @override_settings({'local_aliases': {'_local1': None}})
    def test_update_doesnt_clean_local_aliases(self):
        stdout = self.run_command('update')
        self.assertNotIn('_local1', stdout)
