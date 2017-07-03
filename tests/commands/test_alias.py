from __future__ import unicode_literals

from freezegun import freeze_time


def test_alias_list(cli, config):
    config.clear_section('test_aliases')
    for alias, activity in [('alias_1', '123/456'), ('alias_2', '123/457'),
                            ('foo', '123/458')]:
        config.set('test_aliases', alias, activity)

    output = cli('alias')
    lines = output.splitlines()

    assert lines == [
        "[test] alias_1 -> 123/456",
        "[test] alias_2 -> 123/457",
        "[test] foo -> 123/458",
    ]


def test_alias_search_mapping_exact(cli, config):
    config.clear_section('test_aliases')
    config.set('test_aliases', 'alias_1', '123/456')
    output = cli('alias', ['list', 'alias_1'])
    assert output == "[test] alias_1 -> 123/456\n"


def test_alias_search_mapping_partial(cli, config):
    config.clear_section('test_aliases')
    config.set('test_aliases', 'alias_1', '123/456')
    config.set('test_aliases', 'alias_2', '123/457')

    output = cli('alias', ['list', 'alias'])
    lines = output.splitlines()

    assert lines == [
        "[test] alias_1 -> 123/456",
        "[test] alias_2 -> 123/457"
    ]


def test_alias_search_project(cli, config):
    config.clear_section('test_aliases')
    config.set('test_aliases', 'alias_1', '123/456')
    config.set('test_aliases', 'alias_2', '123/457')
    output = cli('alias', ['list', '-r', '123'])
    lines = output.splitlines()

    assert lines == [
        "[test] 123/456 -> alias_1",
        "[test] 123/457 -> alias_2"
    ]

    output = cli('alias', ['list', '12'])
    lines = output.splitlines()

    assert len(lines) == 0


def test_alias_search_project_activity(cli, config):
    config.clear_section('test_aliases')
    config.set('test_aliases', 'alias_1', '123/456')
    config.set('test_aliases', 'alias_2', '123/457')

    output = cli('alias', ['list', '-r', '123/457'])
    lines = output.splitlines()
    assert len(lines) == 1
    assert "[test] 123/457 -> alias_2" in lines

    output = cli('alias', ['list', '-r', '123/458'])
    lines = output.splitlines()
    assert len(lines) == 0


def test_alias_add(cli, config):
    cli('alias', ['add', '-b', 'test', 'bar', '123/458'])

    with open(config.path, 'r') as f:
        config_lines = f.readlines()

    assert 'bar = 123/458\n' in config_lines


def test_local_alias(cli, config):
    config.set('local_aliases', '__pingpong', '')
    output = cli('alias')
    assert '[local] __pingpong -> not mapped' in output


@freeze_time('2017-06-21')
def test_used_option_only_shows_used_aliases(cli, entries_file, config):
    config.clear_section('test_aliases')
    config.set('test_aliases', 'alias_1', '123/456')
    config.set('test_aliases', 'alias_2', '123/457')

    entries_file.write("""20.06.2017
    alias_2 1 Play ping-pong
    """)

    output = cli('alias', ['list', '--used'])

    assert 'alias_1' not in output
    assert 'alias_2' in output
