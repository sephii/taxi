from __future__ import unicode_literals

import os
import shutil
import tempfile

from freezegun import freeze_time

from . import override_settings, CommandTestCase


class StatusCommandTestCase(CommandTestCase):
    @freeze_time('2014-01-20')
    def test_status_previous_file(self):
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        with self.settings({'default': {'file': self.entries_file}}):
            with freeze_time('2014-01-01'):
                self.write_entries("""01/01/2014
    alias_1 1 january
    """)

            with freeze_time('2014-02-01'):
                self.write_entries("""01/02/2014
    alias_1 1 february
    """)

                stdout = self.run_command('status')
            shutil.rmtree(tmp_entries_dir)

        self.assertIn('january', stdout)
        self.assertIn('february', stdout)

    @override_settings({'local_aliases': {'_pingpong': None}})
    @freeze_time('2014-01-20')
    def test_local_alias(self):
        self.write_entries("""20/01/2014
_pingpong 0800-0900 Play ping-pong
""")
        stdout = self.run_command('status')

        self.assertLineIn(
            "_pingpong (local)  (1.00)  Play ping-pong",
            stdout
        )

    @override_settings({'local_aliases': {
        '_pingpong': None,
        '_coffee': None
    }})
    @freeze_time('2014-01-20')
    def test_multiple_local_aliases(self):
        self.write_entries("""20/01/2014
_pingpong 0800-0900 Play ping-pong
_coffee 0900-1000 Drink some coffee
""")

        stdout = self.run_command('status')
        self.assertLineIn(
            "_pingpong (local)  (1.00)  Play ping-pong",
            stdout
        )
        self.assertLineIn(
            "_coffee (local)    (1.00)  Drink some coffee",
            stdout
        )

    @freeze_time('2014-01-20')
    def test_regrouped_entries(self):
        self.write_entries("""20/01/2014
alias_1 0800-0900 Play ping-pong
alias_1 1200-1300 Play ping-pong
""")

        stdout = self.run_command('status')
        self.assertLineIn(
            "alias_1 (123/456, test)        2.00  Play ping-pong",
            stdout
        )

    @freeze_time('2014-01-20')
    def test_status_ignored_not_mapped(self):
        self.write_entries("""20/01/2014
unmapped? 0800-0900 Play ping-pong
""")

        stdout = self.run_command('status')
        self.assertLineIn(
            "unmapped (ignored)             1.00  Play ping-pong",
            stdout
        )

    @override_settings({'default': {'regroup_entries': '0'}})
    @freeze_time('2014-01-20')
    def test_regroup_entries_setting(self):
        self.write_entries("""20/01/2014
alias_1 0800-0900 Play ping-pong
alias_1 1200-1300 Play ping-pong
""")

        stdout = self.run_command('status')
        self.assertLineIn(
            "alias_1 (123/456, test)        1.00  Play ping-pong",
            stdout
        )
