from . import CommandTestCase


class AliasCommandTestCase(CommandTestCase):
    """
    We can't test exact output in the tests because the aliases returned by the
    `alias` command is a dict and thus is not ordered.
    """
    def setUp(self):
        super(AliasCommandTestCase, self).setUp()

        self.config = self.default_config.copy()
        self.config['wrmap'] = {
            'alias_1': '123/456',
            'alias_2': '123/457',
            'foo': '777/777'
        }

    def run_alias_command(self, args, config_options):
        return self.run_command('alias', args, self.default_options,
                                config_options)

    def test_alias_list(self):
        output = self.run_alias_command([], self.config)
        lines = output.splitlines()

        self.assertEquals(len(lines), 3)
        self.assertIn("alias_1 -> 123/456 (?)", lines)
        self.assertIn("alias_2 -> 123/457 (?)", lines)
        self.assertIn("foo -> 777/777 (?)", lines)

    def test_alias_search_mapping_exact(self):
        output = self.run_alias_command(['alias_1'], self.config)
        self.assertEquals(output, "alias_1 -> 123/456 (?)\n")

    def test_alias_search_mapping_partial(self):
        output = self.run_alias_command(['alias'], self.config)
        lines = output.splitlines()

        self.assertEquals(len(lines), 2)
        self.assertIn("alias_1 -> 123/456 (?)", lines)
        self.assertIn("alias_2 -> 123/457 (?)", lines)

    def test_alias_search_project(self):
        output = self.run_alias_command(['123'], self.config)
        lines = output.splitlines()

        self.assertEquals(len(lines), 2)
        self.assertIn("123/456 -> alias_1 (?)", lines)
        self.assertIn("123/457 -> alias_2 (?)", lines)

        output = self.run_alias_command(['12'], self.config)
        lines = output.splitlines()

        self.assertEquals(len(lines), 0)

    def test_alias_search_project_activity(self):
        output = self.run_alias_command(['123/457'], self.config)
        lines = output.splitlines()
        self.assertEquals(len(lines), 1)
        self.assertIn("123/457 -> alias_2 (?)", lines)

        output = self.run_alias_command(['123/458'], self.config)
        lines = output.splitlines()
        self.assertEquals(len(lines), 0)

    def test_alias_add(self):
        self.run_alias_command(['bar', '123/458'], self.config)

        with open(self.config_file, 'r') as f:
            config_lines = f.readlines()

        self.assertIn('bar = 123/458\n', config_lines)

    def test_local_alias(self):
        self.config = self.default_config.copy()
        self.config['default']['local_aliases'] = 'pingpong'

        stdout = self.run_alias_command([], self.config)
        self.assertIn('pingpong -> local alias', stdout)
