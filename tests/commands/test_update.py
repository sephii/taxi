from . import CommandTestCase, override_settings


class UpdateCommandTestCase(CommandTestCase):
    @override_settings({'default': {'local_aliases': '_local1, _local2'}})
    def test_update_doesnt_clean_local_aliases(self):
        stdout = self.run_command('update')
        self.assertNotIn('_local1', stdout)
