from freezegun import freeze_time

from . import CommandTestCase


class AutofillCommandTestCase(CommandTestCase):
    """
    Tests for the `autofill` command.
    """
    def run_autofill_command(self, config_options=None):
        self.run_command('autofill', config_options=config_options)

    @freeze_time('2012-02-20')
    def test_autofill_bottom(self):
        config_options = self.default_config.copy()
        config_options['default'].update({
            'auto_fill_days': '1',
            'auto_add': 'bottom'
        })

        self.run_autofill_command(config_options)
        entries_file_contents = self.read_entries()

        self.assertEqual(entries_file_contents, """07/02/2012

14/02/2012

21/02/2012

28/02/2012
""")

    @freeze_time('2012-02-20')
    def test_autofill_top(self):
        config_options = self.default_config.copy()
        config_options['default'].update({
            'auto_fill_days': '1',
            'auto_add': 'top'
        })

        self.run_autofill_command(config_options)
        entries_file_contents = self.read_entries()

        self.assertEqual(entries_file_contents, """28/02/2012

21/02/2012

14/02/2012

07/02/2012
""")

    @freeze_time('2012-02-20')
    def test_autofill_existing_entries(self):
        config_options = self.default_config.copy()
        config_options['default'].update({
            'auto_fill_days': '1',
            'auto_add': 'top'
        })

        self.write_entries("15/02/2012\n\n07/02/2012")

        self.run_autofill_command(config_options)
        entries_file_contents = self.read_entries()

        self.assertEqual(entries_file_contents, """28/02/2012

21/02/2012

15/02/2012

07/02/2012
""")
