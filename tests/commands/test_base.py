import os


def test_run_without_config_file_creates_config_file(cli, config):
    os.remove(config.path)
    cli('alias', input=''.join([
        'y\n', 'dummy\n', 'janedoe\n', 'password\n',
        'timesheets.example.com\n', 'vim\n'
    ]))
    assert os.path.exists(config.path)


def test_wizard_constructs_correct_url_with_token(cli, config):
    os.remove(config.path)
    cli('alias', input=''.join([
        'y\n', 'dummy\n', 'token\n', '\n', 'timesheets.example.com\n',
        'vim\n'
    ]))
    with open(config.path, 'r') as f:
        config = f.read()

    assert 'dummy://token@timesheets.example.com' in config
