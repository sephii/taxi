from freezegun import freeze_time

from . import CommandTestCase


@freeze_time('2014-01-20')
class CommitCommandTestCase(CommandTestCase):
    def test_commit(self):
        config = self.default_config
        config['wrmap']['fail'] = '456/789'

        self.write_entries("""20/01/2014
fail     0745-0830  Repair coffee machine
alias_1 -0900 Play ping-pong
alias_1 -0915 Check coffee machine uptime
fail     -1145 Make printer work
fail   1300-1400 Printer is down again
""")
        self.run_command('commit', options=self.default_options)

        with open(self.entries_file, 'r') as entries:
            lines = entries.readlines()

        self.assertEqual(lines[4], 'fail 09:15-11:45 Make printer work\n')
