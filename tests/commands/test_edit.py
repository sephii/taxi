# -*- coding: utf-8 -*-
from freezegun import freeze_time

from . import CommandTestCase


@freeze_time('2014-01-21')
class EditCommandTestCase(CommandTestCase):
    def test_autofill_with_specified_file(self):
        """
        Edit with specified date should not autofill it.
        """
        config = self.default_config.copy()
        options = self.default_options.copy()

        config['default']['auto_fill_days'] = '0,1,2,3,4,5,6'
        options['file'] = self.entries_file

        self.run_command('edit', options=options)

        with open(self.entries_file, 'r') as f:
            self.assertEqual(f.read(), '')

    def test_edit_utf8_file(self):
        """
        Editing a file that contains accents should not crash.
        """
        self.write_entries("""20/01/2014
alias_1 2 préparation du café pour l'évènement
""")
        self.run_command('edit')
