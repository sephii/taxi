from contextlib import nested
from freezegun import freeze_time
from StringIO import StringIO

from taxi.app import Taxi

from . import CommandTest


@freeze_time('2014-01-20')
class StartCommandTest(CommandTest):
    def compare_entries_with_expected(self, entries, expected):
        stdout = StringIO()
        options = {
            'ignore_date_error': True,
            'stdout': stdout
        }

        with nested(self.generate_config_file(self.default_config),
                    self.generate_entries_file(entries)) as (config_file, entries_file):
            options['config'] = config_file.name
            options['file'] = entries_file.name

            app = Taxi()
            app.run_command('start', options=options, args=['alias_1'])

            entries_file.seek(0)
            self.assertEqual(entries_file.read(), expected)

    def test_date_present_entry_present(self):
        entries = """20/01/2014
alias_1 2 foobar
"""
        expected = """20/01/2014
alias_1 2 foobar
alias_1 00:00-? ?
"""
        self.compare_entries_with_expected(entries, expected)

    def test_date_present_entry_not_present(self):
        entries = """20/01/2014
"""
        expected = """20/01/2014

alias_1 00:00-? ?
"""
        self.compare_entries_with_expected(entries, expected)

    def test_date_not_present_entry_not_present(self):
        entries = """19/01/2014
alias_1 2 foo
"""
        expected = """20/01/2014

alias_1 00:00-? ?

19/01/2014
alias_1 2 foo
"""
        self.compare_entries_with_expected(entries, expected)

    def test_use_previous_end_time_as_start_time(self):
        entries = """20/01/2014
alias_1 0900-1000 foobar
"""
        expected = """20/01/2014
alias_1 0900-1000 foobar
alias_1 10:00-? ?
"""
        self.compare_entries_with_expected(entries, expected)
