from . import CommandTestCase


class UpdateCommandTestCase(CommandTestCase):
    def test_update_doesnt_clean_local_aliases(self):
        config = self.default_config.copy()
        config['default']['local_aliases'] = '_local1, _local2'
        self.write_config(config)

        stdout = self.run_command('update')
        self.assertNotIn('_local1', stdout)
