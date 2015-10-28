from __future__ import unicode_literals

from . import CommandTestCase, override_settings


@override_settings()
class AliasCommandTestCase(CommandTestCase):
    """
    We can't test exact output in the tests because the aliases returned by the
    `alias` command is a dict and thus is not ordered.
    """
    def setUp(self):
        super(AliasCommandTestCase, self).setUp()
        self._settings['test_aliases'] = {
            'alias_1': '123/456',
            'alias_2': '123/457',
            'foo': '777/777'
        }

    def run_alias_command(self, args):
        return self.run_command('alias', args)

    def test_alias_list(self):
        output = self.run_alias_command([])
        lines = output.splitlines()

        self.assertEquals(len(lines), 3)
        self.assertIn("[test] alias_1 -> 123/456", lines)
        self.assertIn("[test] alias_2 -> 123/457", lines)
        self.assertIn("[test] foo -> 777/777", lines)

    def test_alias_search_mapping_exact(self):
        output = self.run_alias_command(['alias_1'])
        self.assertEquals(output, "[test] alias_1 -> 123/456\n")

    def test_alias_search_mapping_partial(self):
        output = self.run_alias_command(['alias'])
        lines = output.splitlines()

        self.assertEquals(len(lines), 2)
        self.assertIn("[test] alias_1 -> 123/456", lines)
        self.assertIn("[test] alias_2 -> 123/457", lines)

    def test_alias_search_project(self):
        output = self.run_alias_command(['123'])
        lines = output.splitlines()

        self.assertEquals(len(lines), 2)
        self.assertIn("[test] 123/456 -> alias_1", lines)
        self.assertIn("[test] 123/457 -> alias_2", lines)

        output = self.run_alias_command(['12'])
        lines = output.splitlines()

        self.assertEquals(len(lines), 0)

    def test_alias_search_project_activity(self):
        output = self.run_alias_command(['123/457'])
        lines = output.splitlines()
        self.assertEquals(len(lines), 1)
        self.assertIn("[test] 123/457 -> alias_2", lines)

        output = self.run_alias_command(['123/458'])
        lines = output.splitlines()
        self.assertEquals(len(lines), 0)

    def test_alias_add(self):
        self.run_alias_command(['bar', '123/458', 'test'])

        with open(self.config_file, 'r') as f:
            config_lines = f.readlines()

        self.assertIn('bar = 123/458\n', config_lines)

    @override_settings({'local_aliases': {
        '__pingpong': None
    }})
    def test_local_alias(self):
        stdout = self.run_alias_command([])
        self.assertIn('[local] __pingpong -> not mapped', stdout)
