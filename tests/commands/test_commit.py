import os
import shutil
import tempfile
import datetime

from freezegun import freeze_time

from . import CommandTestCase


@freeze_time('2014-01-21')
class CommitCommandTestCase(CommandTestCase):
    def test_fix_entries_start_time(self):
        config = self.default_config.copy()
        config['wrmap']['fail'] = '456/789'

        self.write_entries("""21/01/2014
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

    def test_commit_date(self):
        options = self.default_options.copy()
        options['date'] = '21.01.2014'

        self.write_entries("""21/01/2014
alias_1 2 foobar

20/01/2014
alias_1 1 previous day entry
""")
        stdout = self.run_command('commit', options=options)
        self.assertNotIn('previous day entry', stdout)

        options = self.default_options.copy()
        stdout = self.run_command('commit', options=options)
        self.assertIn('previous day entry', stdout)

    @freeze_time('2014-01-20')
    def test_ignore_date_error_week_day(self):
        self.write_entries("""19/01/2014
alias_1 2 foobar
""")
        stdout = self.run_command('commit', options=self.default_options)
        self.assertIn('--ignore-date-error', stdout)

    def test_ignore_date_error_previous_day(self):
        self.write_entries("""17/01/2014
alias_1 2 foobar
""")
        stdout = self.run_command('commit', options=self.default_options)
        self.assertIn('--ignore-date-error', stdout)

    def test_commit_previous_file(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        freeze_time('2014-01-21')

        self.write_entries("""17/01/2014
alias_1 2 foobar
""")

        with freeze_time('2014-02-05'):
            self.write_entries("""05/02/2014
    alias_1 4 foobar
    """)

            options = self.default_options.copy()
            options['ignore_date_error'] = True

            stdout = self.run_command('commit', config_options=config,
                    options=options)
        shutil.rmtree(tmp_entries_dir)
        #assert False, stdout
