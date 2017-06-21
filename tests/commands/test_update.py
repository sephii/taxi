def test_update_doesnt_clean_local_aliases(cli, config):
    config.set('local_aliases', '_local1', '')
    stdout = cli('update')
    assert '_local1' not in stdout
