from __future__ import unicode_literals

import os
import shutil
import tempfile

from freezegun import freeze_time

from . import CommandTestCase


class CommitCommandTestCase(CommandTestCase):
    @freeze_time('2014-01-21')
    def test_fix_entries_start_time(self):
        self.write_entries("""21/01/2014
fail     0745-0830  Repair coffee machine
alias_1 -0900 Play ping-pong
alias_1 -0915 Check coffee machine uptime
fail    -1145 Make printer work
fail   1300-1400 Printer is down again
""")
        self.run_command('commit')

        with open(self.entries_file, 'r') as entries:
            lines = entries.readlines()

        self.assertEqual(lines[4], 'fail    0915-1145 Make printer work\n')

    @freeze_time('2014-01-21')
    def test_fix_ignored_entries_start_time(self):
        self.write_entries("""21/01/2014
alias_1     0745-0830  Repair coffee machine
alias_1 -0900 Play ping-pong
ignored_alias -0915 Check coffee machine uptime
ignored_alias -1000 Check coffee machine uptime
""")
        self.run_command('commit')

        with open(self.entries_file, 'r') as entries:
            lines = entries.readlines()

        self.assertEqual(
            lines[3],
            'ignored_alias 0900-0915 Check coffee machine uptime\n'
        )
        self.assertEqual(
            lines[4],
            'ignored_alias -1000 Check coffee machine uptime\n'
        )

    @freeze_time('2014-01-21')
    def test_commit_date(self):
        self.write_entries("""21/01/2014
alias_1 2 foobar

20/01/2014
alias_1 1 previous day entry
""")
        stdout = self.run_command('commit', args=['--date=21.01.2014'])
        self.assertNotIn('previous day entry', stdout)

        stdout = self.run_command('commit')
        self.assertIn('previous day entry', stdout)

    @freeze_time('2014-01-20')
    def test_ignore_date_error_week_day(self):
        self.write_entries("""19/01/2014
alias_1 2 foobar
""")
        stdout = self.run_command('commit')
        self.assertIn('Are you sure', stdout)

    @freeze_time('2014-01-21')
    def test_ignore_date_error_previous_day(self):
        self.write_entries("""17/01/2014
alias_1 2 foobar
""")
        stdout = self.run_command('commit')
        self.assertIn('Are you sure', stdout)

    @freeze_time('2014-01-21')
    def test_commit_previous_file_previous_month(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2014-01-01'):
            self.write_entries("""01/01/2014
alias_1 2 january
""")

        with freeze_time('2014-02-01'):
            self.write_entries("""01/02/2014
    alias_1 4 february
    """)

            stdout = self.run_command('commit', config_options=config,
                                      args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january', stdout)
        self.assertIn('february', stdout)

    @freeze_time('2014-01-21')
    def test_commit_previous_file_previous_year(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2013-11-01'):
            self.write_entries("""01/11/2013
alias_1 2 november
""")

        with freeze_time('2013-12-01'):
            self.write_entries("""01/12/2013
alias_1 2 december
""")

        with freeze_time('2014-01-01'):
            self.write_entries("""01/01/2014
alias_1 4 january
""")

            stdout = self.run_command('commit', config_options=config,
                                      args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertNotIn('november', stdout)
        self.assertIn('december', stdout)
        self.assertIn('january', stdout)

    @freeze_time('2014-01-21')
    def test_commit_previous_files_previous_months(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()
        config['default']['nb_previous_files'] = 2

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2014-01-01'):
            self.write_entries("""01/01/2014
alias_1 2 january
""")

        with freeze_time('2014-02-01'):
            self.write_entries("""01/02/2014
    alias_1 3 february
    """)

        with freeze_time('2014-03-01'):
            self.write_entries("""01/03/2014
alias_1 4 march
""")

            stdout = self.run_command('commit', config_options=config,
                                      args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january', stdout)
        self.assertIn('february', stdout)
        self.assertIn('march', stdout)

    @freeze_time('2014-01-21')
    def test_commit_previous_file_year_format(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()
        config['default']['nb_previous_files'] = 2

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2013-01-01'):
            self.write_entries("""01/01/2013
    alias_1 1 january 2013
    """)

        with freeze_time('2013-02-01'):
            self.write_entries("""01/02/2013
    alias_1 1 february 2013
    """)

        with freeze_time('2014-01-01'):
            self.write_entries("""01/01/2014
alias_1 1 january 2014
""")

        with freeze_time('2014-02-01'):
            self.write_entries("""01/02/2014
alias_1 1 february 2014
""")

            stdout = self.run_command('commit', config_options=config,
                                      args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january 2013', stdout)
        self.assertIn('february 2013', stdout)
        self.assertIn('january 2014', stdout)
        self.assertIn('february 2014', stdout)

    @freeze_time('2014-01-21')
    def test_local_alias(self):
        config = self.default_config.copy()
        config['default']['local_aliases'] = '_pingpong'

        self.write_entries("""20/01/2014
_pingpong 0800-0900 Play ping-pong
""")

        stdout = self.run_command('commit')
        self.assertIn("Total pushed                   0.00", stdout)

    @freeze_time('2014-01-21')
    def test_fix_entries_start_time_without_previous(self):
        self.write_entries("""21/01/2014
fail     -0830  Repair coffee machine
""")
        self.run_command('commit')

        with open(self.entries_file, 'r') as entries:
            lines = entries.readlines()

        self.assertEqual(lines[1], 'fail     -0830  Repair coffee machine\n')

    @freeze_time('2014-01-21')
    def test_failed_aggregated_entries_status(self):
        self.write_entries("""21/01/2014
fail     1  Repair coffee machine
fail     2  Repair coffee machine
""")
        stdout = self.run_command('commit')

        self.assertNotIn('AggregatedTimesheetEntry', stdout)
