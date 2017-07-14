from __future__ import unicode_literals

import datetime

from freezegun import freeze_time

from taxi.timesheet import EntriesCollection, TimesheetParser

from .assertions import line_in
from .conftest import EntriesFileGenerator


@freeze_time('2014-01-21')
def test_commit_date(cli, entries_file):
    entries_file.write("""21/01/2014
alias_1 2 foobar

20/01/2014
alias_1 1 previous day entry
""")
    stdout = cli('commit', args=['--since=21.01.2014', '--until=21.01.2014'])
    assert 'previous day entry' not in stdout

    stdout = cli('commit')
    assert 'previous day entry' in stdout


@freeze_time('2014-01-20')
def test_ignore_date_error_week_day(cli, entries_file):
    entries_file.write("""19/01/2014
alias_1 2 foobar
""")
    stdout = cli('commit')
    assert 'Are you sure' in stdout


@freeze_time('2014-01-21')
def test_ignore_date_error_previous_day(cli, entries_file):
    entries_file.write("""17/01/2014
alias_1 2 foobar
""")
    stdout = cli('commit')
    assert 'Are you sure' in stdout


@freeze_time('2014-02-21')
def test_commit_previous_file_previous_month(cli, data_dir, config):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.tks')
    efg.expand(datetime.date(2014, 1, 1)).write(
        "01/01/2014\nalias_1 2 january"
    )
    efg.expand(datetime.date(2014, 2, 1)).write(
        "01/02/2014\nalias_1 4 february"
    )
    efg.patch_config(config)

    stdout = cli('commit', ['--yes'])

    assert 'january' in stdout
    assert 'february' in stdout


@freeze_time('2014-01-21')
def test_commit_previous_file_previous_year(cli, data_dir, config):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.tks')
    efg.expand(datetime.date(2013, 11, 1)).write(
        "01/11/2013\nalias_1 2 november"
    )
    efg.expand(datetime.date(2013, 12, 1)).write(
        "01/12/2013\nalias_1 2 december"
    )
    efg.expand(datetime.date(2014, 1, 1)).write(
        "01/01/2014\nalias_1 4 january"
    )
    efg.patch_config(config)

    stdout = cli('commit', args=['--yes'])

    assert 'november' not in stdout
    assert 'december' in stdout
    assert 'january' in stdout


@freeze_time('2014-01-21')
def test_commit_previous_files_previous_months(cli, data_dir, config):
    config.set('taxi', 'nb_previous_files', '2')

    efg = EntriesFileGenerator(data_dir, '%m_%Y.tks')
    efg.expand(datetime.date(2013, 11, 1)).write(
        "01/11/2013\nalias_1 2 november"
    )
    efg.expand(datetime.date(2013, 12, 1)).write(
        "01/12/2013\nalias_1 2 december"
    )
    efg.expand(datetime.date(2014, 1, 1)).write(
        "01/01/2014\nalias_1 4 january"
    )
    efg.patch_config(config)

    stdout = cli('commit', args=['--yes'])

    assert 'november' in stdout
    assert 'december' in stdout
    assert 'january' in stdout


@freeze_time('2014-01-21')
def test_commit_previous_file_year_format(cli, data_dir, config):
    config.set('taxi', 'nb_previous_files', '2')

    efg = EntriesFileGenerator(data_dir, '%Y.tks')
    efg.expand(datetime.date(2013, 1, 1)).write(
        "01/01/2013\nalias_1 1 january 2013"
    )
    efg.expand(datetime.date(2013, 2, 1)).write(
        "01/02/2013\nalias_1 1 february 2013", mode='a'
    )
    efg.expand(datetime.date(2014, 1, 1)).write(
        "01/01/2014\nalias_1 1 january 2014"
    )
    efg.expand(datetime.date(2014, 2, 1)).write(
        "01/02/2014\nalias_1 1 february 2014", mode='a'
    )
    efg.patch_config(config)
    stdout = cli('commit', args=['--yes'])

    assert 'january 2013' in stdout
    assert 'february 2013' in stdout
    assert 'january 2014' in stdout
    assert 'february 2014' in stdout


@freeze_time('2014-01-21')
def test_local_alias(cli, config, entries_file):
    config.set('local_aliases', '_pingpong', '')
    entries_file.write("""20/01/2014
_pingpong 0800-0900 Play ping-pong
""")

    stdout = cli('commit')
    assert line_in("Total pushed, local  1.00", stdout)


@freeze_time('2014-01-21')
def test_fix_entries_start_time_without_previous(cli, entries_file):
    entries_file.write("""21/01/2014
fail     -0830  Repair coffee machine
""")
    cli('commit')

    lines = entries_file.readlines()

    assert lines[1] == 'fail     -0830  Repair coffee machine\n'


@freeze_time('2014-01-21')
def test_failed_aggregated_entries_status(cli, entries_file):
    entries_file.write("""21/01/2014
fail     1  Repair coffee machine
fail     2  Repair coffee machine
""")
    stdout = cli('commit')

    assert 'AggregatedTimesheetEntry' not in stdout


@freeze_time('2014-01-21')
def test_not_today_option(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 2 Play ping-pong

21/01/2014
alias_1     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
    stdout = cli('commit', args=['--not-today'])

    assert 'coffee' not in stdout


@freeze_time('2014-01-21')
def test_not_today_option_with_date(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 2 Play ping-pong

21/01/2014
alias_1     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
    stdout = cli('commit', args=[
        '--not-today', '--since=19.01.2014', '--until=21.01.2014']
    )

    assert 'coffee' not in stdout


@freeze_time('2014-01-21')
def test_relative_date(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 2 Play ping-pong

21/01/2014
alias_1     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
    stdout = cli('commit', args=['--until=yesterday'])

    assert 'coffee' not in stdout


@freeze_time('2014-01-21')
def test_post_push_fail(cli, entries_file):
    entries_file.write("""21/01/2014
post_push_fail     1  Repair coffee machine
alias_1     2  Repair coffee machine
""")
    stdout = cli('commit')

    assert 'Failed entries\n\npost_push_fail' in stdout


@freeze_time('2014-01-21')
def test_successful_push_doesnt_show_failed_entries(cli, entries_file):
    entries_file.write("""21/01/2014
alias_1 2 Play ping-pong
""")
    stdout = cli('commit')

    assert 'Failed entries' not in stdout


@freeze_time('2014-01-22')
def test_commit_confirmation_date_order(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 2 Play ping-pong

18/01/2014
alias_1 2 Play ping-pong

19/01/2014
alias_1 1 Play ping-pong
""")
    stdout = cli('commit', input='y').splitlines()
    dates = [stdout[2], stdout[4], stdout[6]]
    assert dates[0].endswith('18 January')
    assert dates[1].endswith('19 January')
    assert dates[2].endswith('20 January')


@freeze_time('2014-01-21')
def test_regroup_entries_setting(cli, config, entries_file):
    config.set('taxi', 'regroup_entries', '0')
    entries_file.write("""20/01/2014
alias_1 0800-0900 Play ping-pong
alias_1 1200-1300 Play ping-pong
""")

    stdout = cli('commit')
    assert line_in(
        "alias_1 1.00  Play ping-pong",
        stdout
    )


@freeze_time('2017-07-03')
def test_failed_entry_doesnt_change_continuation_entry_time(cli, entries_file):
    entries_file.write("""03/07/2017
alias_1 0800-0900 Using a correct alias
fail  -1000 And a failing alias
""")
    cli('commit')

    entries = EntriesCollection(TimesheetParser(), entries=entries_file.read())[datetime.date(2017, 7, 3)]

    assert entries[0].pushed
    assert not entries[1].pushed
    assert entries[1].duration == (None, datetime.time(10))
