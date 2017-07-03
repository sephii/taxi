from __future__ import unicode_literals

from six.moves import configparser


def test_migration_to_43_copies_default_section(cli, config):
    config.config.remove_section('taxi')
    config.save()
    with open(config.path, 'a') as config_fp:
        config_fp.write('[default]\neditor = /bin/false\n')

    cli('status')

    cp = configparser.RawConfigParser()
    cp.read(config.path)

    assert not cp.has_section('default')
    assert cp.get('taxi', 'editor') == '/bin/false'
