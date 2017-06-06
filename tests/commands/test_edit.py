# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from freezegun import freeze_time

from .conftest import EntriesFileGenerator


def test_autofill_with_specified_file(cli, config, entries_file):
    """
    Edit with specified date should not autofill it.
    """
    config.set('taxi', 'auto_fill_days', '0,1,2,3,4,5,6')
    cli('edit', args=['--file=%s' % str(entries_file)])

    assert entries_file.read() == ''


def test_edit_utf8_file(cli, config, entries_file):
    """
    Editing a file that contains accents should not crash.
    """
    # I wish I could just `entries_file.write()` without encoding anything but... Python 2
    entries_file.write_binary(
        "20/01/2014\nalias_1 2 préparation du café pour l'évènement".encode('utf-8')
    )

    cli('edit')


def test_edit_status(cli, config, data_dir):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        "20/01/2014\nalias_1 2 hello world"
    )
    efg.expand(datetime.date(2014, 2, 21)).write(
        "20/02/2014\nalias_1 2 hello world"
    )
    efg.patch_config(config)

    with freeze_time('2014-01-21'):
        stdout = cli('edit')

    assert 'Monday 20 january' in stdout


def test_prefill_entries_add_to_bottom(cli, data_dir, config):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        """20/01/2014
alias_1 2 hello world

21/01/2014
alias_1 1 foo bar""")
    efg.expand(datetime.date(2014, 2, 21)).write(
        "20/02/2014\nalias_1 2 hello world"
    )
    efg.patch_config(config)

    with freeze_time('2014-02-21'):
        cli('edit')

    lines = efg.expand(datetime.date(2014, 2, 21)).readlines()

    assert '20/02/2014\n' == lines[0]
    assert '21/02/2014\n' == lines[3]


def test_previous_file_doesnt_autofill(cli, data_dir, config):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        """20/01/2014
alias_1 2 hello world

21/01/2014
alias_1 1 foo bar""")
    efg.expand(datetime.date(2014, 2, 21)).write(
        "20/02/2014\nalias_1 2 hello world"
    )
    efg.patch_config(config)

    cli('edit', args=['1'])

    lines = efg.expand(datetime.date(2014, 2, 21)).readlines()

    assert '21/02/2014\n' not in lines


def test_autofill_adds_initial_data(cli, data_dir, config):
    efg = EntriesFileGenerator(data_dir, '%m_%Y.txt')
    efg.expand(datetime.date(2014, 1, 21)).write(
        """20/01/2014
= alias_1 2 hello world
= alias_2 1 hello world
= alias_2 1 hello world
""")
    efg.patch_config(config)

    with freeze_time('2014-02-01'):
        cli('edit')

    with open(str(efg.expand(datetime.date(2014, 2, 1))), 'r') as fp:
        new_file_contents = fp.readlines()

    assert new_file_contents == ['# Recently used aliases:\n', '# alias_2\n', '# alias_1\n']
