from freezegun import freeze_time


@freeze_time('2012-02-20')
def test_autofill_bottom(cli, config, entries_file):
    config.set_dict({
        'taxi': {
            'auto_fill_days': '1',
            'auto_add': 'bottom'
        }
    })

    cli('autofill')
    entries_file_contents = entries_file.readlines()

    assert entries_file_contents == [
        "07/02/2012\n", "\n", "14/02/2012\n", "\n", "21/02/2012\n", "\n",
        "28/02/2012\n"
    ]


@freeze_time('2012-02-20')
def test_autofill_top(cli, config, entries_file):
    config.set_dict({
        'taxi': {
            'auto_fill_days': '1',
            'auto_add': 'top'
        }
    })

    cli('autofill')
    entries_file_contents = entries_file.readlines()

    assert entries_file_contents == [
        "28/02/2012\n", "\n", "21/02/2012\n", "\n", "14/02/2012\n", "\n",
        "07/02/2012\n"
    ]


@freeze_time('2012-02-20')
def test_autofill_existing_entries(cli, config, entries_file):
    config.set_dict({
        'taxi': {
            'auto_fill_days': '1',
            'auto_add': 'top'
        }
    })

    entries_file.write("15/02/2012\n\n07/02/2012")
    cli('autofill')
    entries_file_contents = entries_file.readlines()

    assert entries_file_contents == [
        "28/02/2012\n", "\n", "21/02/2012\n", "\n", "15/02/2012\n", "\n",
        "07/02/2012\n"
    ]
