import configparser


def test_migration_to_51_removes_shared_aliases(cli, config):
    config.set('test_shared_aliases', 'foo', '123/456')

    cli('status')

    cp = configparser.RawConfigParser()
    cp.read(config.path)

    assert not cp.has_section('test_shared_aliases')
