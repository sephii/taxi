import datetime

from freezegun import freeze_time

from .assertions import line_in
from .conftest import EntriesFileGenerator


@freeze_time('2014-02-20')
def test_status_previous_file(cli, config, data_dir):
    config.set('taxi', 'nb_previous_files', '1')
    efg = EntriesFileGenerator(data_dir, '%m_%Y.tks')
    efg.expand(datetime.date(2014, 1, 1)).write(
        "01/01/2014\nalias_1 1 january"
    )
    efg.expand(datetime.date(2014, 2, 1)).write(
        "01/02/2014\nalias_1 1 february"
    )
    efg.patch_config(config)

    stdout = cli('status')

    assert 'january' in stdout
    assert 'february' in stdout


@freeze_time('2014-01-20')
def test_local_alias(cli, config, entries_file):
    config.set('local_aliases', '_pingpong', '')

    entries_file.write("""20/01/2014
_pingpong 0800-0900 Play ping-pong
""")
    stdout = cli('status')

    assert line_in("_pingpong  ( 1.00)  Play ping-pong", stdout)


@freeze_time('2014-01-20')
def test_multiple_local_aliases(cli, config, entries_file):
    config.set_dict({'local_aliases': {'_pingpong': '', '_coffee': ''}})
    entries_file.write("""20/01/2014
_pingpong 0800-0900 Play ping-pong
_coffee 0900-1000 Drink some coffee
""")

    stdout = cli('status')
    assert line_in(
        "_pingpong  ( 1.00)  Play ping-pong",
        stdout
    )
    assert line_in(
        "_coffee    ( 1.00)  Drink some coffee",
        stdout
    )


@freeze_time('2014-01-20')
def test_regrouped_entries(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 0800-0900 Play ping-pong
alias_1 1200-1300 Play ping-pong
""")

    stdout = cli('status')
    assert line_in(
        "alias_1 2.00  Play ping-pong",
        stdout
    )


@freeze_time('2014-01-20')
def test_status_ignored_not_mapped(cli, entries_file):
    entries_file.write("""20/01/2014
? unmapped 0800-0900 Play ping-pong
""")

    stdout = cli('status')
    assert line_in(
        "unmapped (ignored, inexistent alias) 1.00  Play ping-pong",
        stdout
    )


@freeze_time('2014-01-20')
def test_regroup_entries_setting(cli, config, entries_file):
    config.set('taxi', 'regroup_entries', '0')
    entries_file.write("""20/01/2014
alias_1 0800-0900 Play ping-pong
alias_1 1200-1300 Play ping-pong
""")

    stdout = cli('status')
    assert line_in(
        "alias_1        1.00  Play ping-pong",
        stdout
    )


@freeze_time('2014-01-20')
def test_status_doesnt_show_pushed_entries(cli, config, entries_file):
    config.set_dict({
        'test_aliases': {'alias_1': '123/456', 'alias_2': '456/789'}
    })
    entries_file.write("""20/01/2014
= alias_1 0800-0900 Play ping-pong
alias_2 1200-1300 Play ping-pong
""")

    stdout = cli('status')

    assert 'alias_1' not in stdout


@freeze_time('2014-01-20')
def test_status_pushed_option_shows_pushed_entries(cli, config, entries_file):
    config.set_dict({
        'test_aliases': {'alias_1': '123/456', 'alias_2': '456/789'}
    })
    entries_file.write("""20/01/2014
= alias_1 0800-0900 Play ping-pong
alias_2 1200-1300 Play ping-pong
""")

    stdout = cli('status', ['--pushed'])
    assert 'alias_1' in stdout


def test_since_and_until_parameters_limit_dates_to_boundaries(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 1 Invisible entry

21/01/2014
alias_1 1 Visible entry

22/01/2014
alias_1 1 Visible entry

23/01/2014
alias_1 1 Invisible entry
""")
    stdout = cli('status', ['--since=21.01.2014', '--until=22.01.2014'])

    assert 'Invisible entry' not in stdout


@freeze_time('2014-01-21')
def test_today_only_shows_todays_entries(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 1 Invisible entry

21/01/2014
alias_1 1 Visible entry

22/01/2014
alias_1 1 Invisible entry

23/01/2014
alias_1 1 Invisible entry
""")
    stdout = cli('status', ['--today'])

    assert 'Invisible entry' not in stdout
    assert 'Visible entry' in stdout


@freeze_time('2014-01-21')
def test_not_today_excludes_todays_entries(cli, entries_file):
    entries_file.write("""20/01/2014
alias_1 1 Visible entry

21/01/2014
alias_1 1 Invisible entry

22/01/2014
alias_1 1 Visible entry

23/01/2014
alias_1 1 Visible entry
""")
    stdout = cli('status', ['--not-today'])

    assert 'Invisible entry' not in stdout
    assert 'Visible entry' in stdout
