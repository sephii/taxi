from __future__ import unicode_literals

from freezegun import freeze_time


def test_date_present_entry_present(cli, entries_file):
    entries = """20/01/2014
alias_1 2 foobar
"""
    expected = """20/01/2014
alias_1 2 foobar
alias_1 00:00-? ?
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20'):
        cli('start', ['alias_1'])

    assert entries_file.read() == expected


def test_date_present_entry_not_present(cli, entries_file):
    entries = """20/01/2014
"""
    expected = """20/01/2014

alias_1 00:00-? ?
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20'):
        cli('start', ['alias_1'])

    assert entries_file.read() == expected


def test_date_not_present_entry_not_present(cli, entries_file):
    entries = """19/01/2014
alias_1 2 foo
"""
    expected = """20/01/2014

alias_1 00:00-? ?

19/01/2014
alias_1 2 foo
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20'):
        cli('start', ['alias_1'])

    assert entries_file.read() == expected


def test_use_previous_end_time_as_start_time(cli, entries_file):
    entries = """20/01/2014
alias_1 09:00-10:00 foobar
"""
    expected = """20/01/2014
alias_1 09:00-10:00 foobar
alias_1 10:00-? ?
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20'):
        cli('start', ['alias_1'])
    assert entries_file.read() == expected
