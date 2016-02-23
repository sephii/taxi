import os

from . import CommandTestCase


class BaseCommandTestCase(CommandTestCase):
    def test_run_without_config_file_creates_config_file(self):
        os.remove(self.config_file)
        self.run_command('alias', write_config=False, input=''.join([
            'y\n', 'dummy\n', 'janedoe\n', 'password\n', 'vim\n',
            'timesheets.example.com\n'
        ]))
        self.assertTrue(os.path.exists(self.config_file))

    def test_wizard_constructs_correct_url_with_token(self):
        os.remove(self.config_file)
        self.run_command('alias', write_config=False, input=''.join([
            'y\n', 'dummy\n', 'token\n', '\n', 'vim\n',
            'timesheets.example.com\n'
        ]))
        with open(self.config_file, 'r') as f:
            config = f.read()

        self.assertIn('dummy://token@timesheets.example.com', config)
