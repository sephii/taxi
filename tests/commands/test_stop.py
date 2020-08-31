from freezegun import freeze_time


def test_description_entry_present(cli, entries_file):
    entries = """20/01/2014
alias_1 10:00-? Play tennis
"""
    expected = """20/01/2014
alias_1 10:00-10:15 Play ping-pong
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20 10:10:00'):
        cli('stop', ['Play ping-pong'])

    assert entries_file.read() == expected


def test_round_next_quarter(cli, entries_file):
    entries = """20/01/2014
alias_1 10:00-? ?
"""
    expected = """20/01/2014
alias_1 10:00-10:15 Play ping-pong
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20 10:01:00'):
        cli('stop', ['Play ping-pong'])

    assert entries_file.read() == expected


def test_round_with_custom_duration(cli, entries_file, config):
    config.set('taxi', 'round_entries', '5')

    entries = """20/01/2014
alias_1 10:00-? ?
"""
    expected = """20/01/2014
alias_1 10:00-10:05 Play ping-pong
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20 10:01:00'):
        cli('stop', ['Play ping-pong'])

    assert entries_file.read() == expected


def test_stop_in_the_past(cli, entries_file):
    entries = """20/01/2014
alias_1 10:00-? ?
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20 09:30:00'):
        output = cli('stop', ['Play ping-pong'])

    assert output == 'Error: You are trying to stop an activity in the future\n'


def test_stop_without_activity_started(cli, entries_file):
    entries = """20/01/2014
alias_1 10:00-10:30 Play ping-pong
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20 10:15:00'):
        output = cli('stop', ['Play ping-pong'])

    assert output == "Error: You don't have any activity in progress for today\n"


def test_stop_with_non_parsable_entry(cli, entries_file):
    entries = """20/01/2014
alias 10:00-ff:ff Play ping-pong
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20'):
        output = cli('stop', ['Play ping-pong'])

    assert output.startswith('Error:')


def test_stop_with_chained_duration(cli, entries_file):
    entries = """20/01/2014
alias_1 09:00-10:00 foobar
alias_1 -? baz
"""
    expected = """20/01/2014
alias_1 09:00-10:00 foobar
alias_1 -11:00 baz
"""

    entries_file.write(entries)
    with freeze_time('2014-01-20 11:00:00'):
        cli('stop')
    assert entries_file.read() == expected
