# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import tempfile

from freezegun import freeze_time

from taxi.utils.file import expand_filename

from . import CommandTestCase


class EditCommandTestCase(CommandTestCase):
    @freeze_time('2014-01-21')
    def test_autofill_with_specified_file(self):
        """
        Edit with specified date should not autofill it.
        """
        config = self.default_config.copy()
        config['default']['auto_fill_days'] = '0,1,2,3,4,5,6'

        self.run_command('edit', args=['--file=%s' % self.entries_file])

        with open(self.entries_file, 'r') as f:
            self.assertEqual(f.read(), '')

    @freeze_time('2014-01-21')
    def test_edit_utf8_file(self):
        """
        Editing a file that contains accents should not crash.
        """
        self.write_entries("""20/01/2014
alias_1 2 préparation du café pour l'évènement
""")
        self.run_command('edit')

    def test_edit_status(self):
        config = self.default_config.copy()
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2014-01-21'):
            self.write_entries("""20/01/2014
alias_1 2 hello world
""")

        with freeze_time('2014-02-21'):
            self.write_entries("""20/02/2014
alias_1 2 hello world
""")

            stdout = self.run_command('edit', config_options=config)
            self.assertIn('Monday 20 january', stdout)

    def test_prefill_entries_add_to_bottom(self):
        config = self.default_config.copy()
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2014-01-21'):
            self.write_entries("""20/01/2014
alias_1 2 hello world

21/01/2014
alias_1 1 foo bar
""")

        with freeze_time('2014-02-21'):
            self.write_entries("""20/02/2014
alias_1 2 hello world
""")
            self.run_command('edit', config_options=config)

            with open(expand_filename(self.entries_file), 'r') as f:
                lines = f.readlines()

            self.assertEqual('20/02/2014\n', lines[0])
            self.assertEqual('21/02/2014\n', lines[3])

    def test_previous_file_argument(self):
        config = self.default_config.copy()
        tmp_entries_dir = tempfile.mkdtemp()
        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2014-01-21'):
            self.write_entries("""20/01/2014
alias_1 2 hello world

21/01/2014
alias_1 1 foo bar
""")

        with freeze_time('2014-02-21'):
            self.write_entries("""20/02/2014
alias_1 2 hello world
""")
            self.run_command('edit', args=['1'], config_options=config)

            with open(expand_filename(self.entries_file), 'r') as f:
                lines = f.readlines()

            self.assertNotIn('20/20/2014\n', lines)
