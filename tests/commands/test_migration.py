from __future__ import unicode_literals

from taxi.settings import Settings


def test_migration_to_41_copies_local_aliases(cli, config):
    config.set('default', 'local_aliases', '_foo, _bar')

    stdout = cli('alias', ['list', '_foo'])
    assert '[local] _foo -> not mapped' in stdout

    settings = Settings(config.path)
    assert settings.config.has_section('local_aliases')
    assert settings.config.has_option('local_aliases', '_foo')
    assert settings.config.get('local_aliases', '_foo') is None
    assert settings.config.has_option('local_aliases', '_bar')
    assert settings.config.get('local_aliases', '_bar') is None
