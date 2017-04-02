from __future__ import unicode_literals

import os
import shutil
import tempfile

from freezegun import freeze_time

from . import CommandTestCase, override_settings


class CommitCommandTestCase(CommandTestCase):
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
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        with self.settings({'default': {'file': self.entries_file}}):
            with freeze_time('2014-01-01'):
                self.write_entries("""01/01/2014
    alias_1 2 january
    """)

            with freeze_time('2014-02-01'):
                self.write_entries("""01/02/2014
        alias_1 4 february
        """)

                stdout = self.run_command('commit', args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january', stdout)
        self.assertIn('february', stdout)

    @freeze_time('2014-01-21')
    def test_commit_previous_file_previous_year(self):
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')

        with self.settings({'default': {'file': self.entries_file}}):
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

                stdout = self.run_command('commit', args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertNotIn('november', stdout)
        self.assertIn('december', stdout)
        self.assertIn('january', stdout)

    @override_settings({'default': {'nb_previous_files': 2}})
    @freeze_time('2014-01-21')
    def test_commit_previous_files_previous_months(self):
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')

        with self.settings({'default': {'file': self.entries_file}}):
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

                stdout = self.run_command('commit', args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january', stdout)
        self.assertIn('february', stdout)
        self.assertIn('march', stdout)

    @override_settings({'default': {'nb_previous_files': 2}})
    @freeze_time('2014-01-21')
    def test_commit_previous_file_year_format(self):
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%Y.txt')

        with self.settings({'default': {'file': self.entries_file}}):
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

                stdout = self.run_command('commit', args=['--yes'])
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january 2013', stdout)
        self.assertIn('february 2013', stdout)
        self.assertIn('january 2014', stdout)
        self.assertIn('february 2014', stdout)

    @override_settings({'default': {'local_aliases': '_pingpong'}})
    @freeze_time('2014-01-21')
    def test_local_alias(self):
        self.write_entries("""20/01/2014
_pingpong 0800-0900 Play ping-pong
""")

        stdout = self.run_command('commit')
        self.assertLineIn("Total pushed, local  1.00", stdout)

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

    @freeze_time('2014-01-21')
    def test_not_today_option(self):
        self.write_entries("""20/01/2014
alias_1 2 Play ping-pong

21/01/2014
alias_1     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
        stdout = self.run_command('commit', args=['--not-today'])

        self.assertNotIn('coffee', stdout)

    @freeze_time('2014-01-21')
    def test_not_today_option_with_date(self):
        self.write_entries("""20/01/2014
alias_1 2 Play ping-pong

21/01/2014
alias_1     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
        stdout = self.run_command('commit', args=[
            '--not-today', '--date=19.01.2014-21.01.2014']
        )

        self.assertNotIn('coffee', stdout)

    @freeze_time('2014-01-21')
    def test_relative_date(self):
        self.write_entries("""20/01/2014
alias_1 2 Play ping-pong

21/01/2014
alias_1     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
        stdout = self.run_command('commit', args=['--date=yesterday'])

        self.assertNotIn('coffee', stdout)

    @freeze_time('2014-01-21')
    def test_post_push_fail(self):
        self.write_entries("""21/01/2014
post_push_fail     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
        stdout = self.run_command('commit')

        self.assertIn('Failed entries\n\npost_push_fail', stdout)

    @freeze_time('2014-01-21')
    def test_successful_push_doesnt_show_failed_entries(self):
        self.write_entries("""21/01/2014
alias_1 2 Play ping-pong
""")
        stdout = self.run_command('commit')

        self.assertNotIn('Failed entries', stdout)

    @freeze_time('2014-01-22')
    def test_commit_confirmation_date_order(self):
        self.write_entries("""20/01/2014
alias_1 2 Play ping-pong

18/01/2014
alias_1 2 Play ping-pong

19/01/2014
alias_1 1 Play ping-pong
""")
        stdout = self.run_command('commit', input='y').splitlines()
        dates = [stdout[2], stdout[4], stdout[6]]
        self.assertTrue(dates[0].endswith('18 January'))
        self.assertTrue(dates[1].endswith('19 January'))
        self.assertTrue(dates[2].endswith('20 January'))

    @freeze_time('2014-01-21')
    def test_regroup_entries_setting(self):
        self.write_entries("""20/01/2014
alias_1 0800-0900 Play ping-pong
alias_1 1200-1300 Play ping-pong
""")

        with self.settings({'default': {'regroup_entries': '0'}}):
            stdout = self.run_command('commit')
        self.assertLineIn(
            "alias_1        1.00  Play ping-pong",
            stdout
        )
