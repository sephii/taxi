from __future__ import unicode_literals

from freezegun import freeze_time

from . import CommandTestCase, override_settings


class AutofillCommandTestCase(CommandTestCase):
    """
    Tests for the `autofill` command.
    """
    def run_autofill_command(self):
        self.run_command('autofill')

    @override_settings({'default': {
        'auto_fill_days': '1',
        'auto_add': 'bottom'
    }})
    @freeze_time('2012-02-20')
    def test_autofill_bottom(self):
        self.run_autofill_command()
        entries_file_contents = self.read_entries()

        self.assertEqual(entries_file_contents, """07/02/2012

14/02/2012

21/02/2012

28/02/2012
""")

    @override_settings({'default': {
        'auto_fill_days': '1',
        'auto_add': 'top'
    }})
    @freeze_time('2012-02-20')
    def test_autofill_top(self):
        self.run_autofill_command()
        entries_file_contents = self.read_entries()

        self.assertEqual(entries_file_contents, """28/02/2012

21/02/2012

14/02/2012

07/02/2012
""")

    @override_settings({'default': {
        'auto_fill_days': '1',
        'auto_add': 'top'
    }})
    @freeze_time('2012-02-20')
    def test_autofill_existing_entries(self):
        self.write_entries("15/02/2012\n\n07/02/2012")

        self.run_autofill_command()
        entries_file_contents = self.read_entries()

        self.assertEqual(entries_file_contents, """28/02/2012

21/02/2012

15/02/2012

07/02/2012
""")
