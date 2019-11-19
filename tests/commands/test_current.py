import datetime
import os

from freezegun import freeze_time

from .conftest import EntriesFileGenerator


def test_current_shows_current_entry(cli, config, data_dir):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        "20/01/2014\nalias_1 1000-? hello world"
    )
    efg.patch_config(config)

    with freeze_time('2014-01-20 10:45:00'):
        stdout = cli('current')

    assert stdout.strip() == "alias_1 00h45m"


def test_current_uses_custom_format(cli, config, data_dir):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        "20/01/2014\nalias_1 1000-? hello world"
    )
    efg.patch_config(config)

    with freeze_time('2014-01-20 10:45:00'):
        stdout = cli('current', args=['--format={alias} {description} {start_time} {hours} {minutes}'])

    assert stdout.strip() == "alias_1 hello world 10:00 0 45"


def test_current_fails_with_exit_code_1_when_no_current_entry(cli, config, data_dir):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        "20/01/2014\nalias_1 5 hello world"
    )
    efg.patch_config(config)

    with freeze_time('2014-01-20 10:45:00'):
        result = cli('current', return_stdout=False)

    assert result.exit_code == 1
    assert result.output.strip() == "No entry in progress."


def test_entry_uses_custom_timesheet(cli, data_dir):
    file_path = os.path.join(str(data_dir), 'timesheet.tks')
    with open(file_path, 'w') as f:
        f.write(
            "20/01/2014\nalias_1 1000-? hello world"
        )

    with freeze_time('2014-01-20 10:45:00'):
        stdout = cli('current', args=['-f%s' % file_path])

    assert stdout.strip() == "alias_1 00h45m"
