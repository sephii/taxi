from __future__ import unicode_literals

from freezegun import freeze_time

from . import CommandTestCase


class StartCommandTestCase(CommandTestCase):
    def compare_entries_with_expected(self, entries, expected):
        options = self.default_options
        options['ignore_date_error'] = True

        self.write_entries(entries)

        self.run_command('start', ['alias_1'], options)

        with open(self.entries_file, 'r') as f:
            self.assertEqual(f.read(), expected)

    @freeze_time('2014-01-20')
    def test_date_present_entry_present(self):
        entries = """20/01/2014
alias_1 2 foobar
"""
        expected = """20/01/2014
alias_1 2 foobar
alias_1 00:00-? ?
"""
        self.compare_entries_with_expected(entries, expected)

    @freeze_time('2014-01-20')
    def test_date_present_entry_not_present(self):
        entries = """20/01/2014
"""
        expected = """20/01/2014

alias_1 00:00-? ?
"""
        self.compare_entries_with_expected(entries, expected)

    @freeze_time('2014-01-20')
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

    @freeze_time('2014-01-20')
    def test_use_previous_end_time_as_start_time(self):
        entries = """20/01/2014
alias_1 09:00-10:00 foobar
"""
        expected = """20/01/2014
alias_1 09:00-10:00 foobar
alias_1 10:00-? ?
"""
        self.compare_entries_with_expected(entries, expected)
