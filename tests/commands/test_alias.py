import pytest
from click import style
from freezegun import freeze_time

from taxi.projects import Activity, Project, ProjectsDb


@pytest.fixture
def projects_db(data_dir):
    projects_db = ProjectsDb(str(data_dir))
    projects_list = []

    project = Project(42, 'not started project', Project.STATUS_NOT_STARTED)
    project.backend = 'test'
    project.activities.append(Activity(1, 'activity 1'))
    project.activities.append(Activity(2, 'activity 2'))
    projects_list.append(project)

    project = Project(43, 'active project', Project.STATUS_ACTIVE)
    project.backend = 'test'
    project.activities.append(Activity(1, 'activity 1'))
    project.activities.append(Activity(2, 'activity 2'))
    projects_list.append(project)

    project = Project(44, '2nd active project', Project.STATUS_ACTIVE)
    project.backend = 'test'
    project.activities.append(Activity(1, 'activity 1'))
    projects_list.append(project)

    project = Project(45, '3rd active project with one inactive activity', Project.STATUS_ACTIVE)
    project.backend = 'test'
    project.activities.append(Activity(3, 'activity 3'))
    project.activities.append(Activity(4, 'activity 4', False))
    projects_list.append(project)

    projects_db.update(projects_list)

    return projects_db


@pytest.fixture
def alias_config(config, projects_db):
    config.clear_section('test_aliases')

    aliases = [
        ('inactive1', '42/1'), ('inactive2', '42/2'), ('active1', '43/1'), ('active2', '43/2'), ('p2_active', '44/1'), ('p3_active_activity', '45/3'), ('p3_inactive_activity', '45/4')
    ]

    for alias, activity in aliases:
        config.set('test_aliases', alias, activity)

    return config


def test_alias_without_parameter_forwards_to_list(cli, alias_config):
    output = cli('alias')
    lines = output.splitlines()

    assert lines == [
        "[test] active1 -> 43/1 (active project, activity 1)",
        "[test] active2 -> 43/2 (active project, activity 2)",
        "[test] inactive1 -> 42/1 (not started project, activity 1)",
        "[test] inactive2 -> 42/2 (not started project, activity 2)",
        "[test] p2_active -> 44/1 (2nd active project, activity 1)",
        "[test] p3_active_activity -> 45/3 (3rd active project with one inactive activity, activity 3)",
        "[test] p3_inactive_activity -> 45/4 (3rd active project with one inactive activity, activity 4)",
    ]


def test_alias_search_mapping_exact(cli, alias_config):
    output = cli('alias', ['list', '--no-inactive', 'active1'])
    assert output == "[test] active1 -> 43/1 (active project, activity 1)\n"


def test_alias_search_mapping_partial(cli, alias_config):
    output = cli('alias', ['list', '--no-inactive', 'active'])
    lines = output.splitlines()

    assert lines == [
        "[test] active1 -> 43/1 (active project, activity 1)",
        "[test] active2 -> 43/2 (active project, activity 2)",
        "[test] p2_active -> 44/1 (2nd active project, activity 1)",
        "[test] p3_active_activity -> 45/3 (3rd active project with one inactive activity, activity 3)",
    ]


def test_alias_search_inactive_listed_in_red(cli, alias_config):
    output = cli("alias", ["list", "inactive"], color=True)
    lines = output.splitlines()

    assert lines == [
        style("[test] inactive1 -> 42/1 (not started project, activity 1)", fg="red"),
        style("[test] inactive2 -> 42/2 (not started project, activity 2)", fg="red"),
        style("[test] p3_inactive_activity -> 45/4 (3rd active project with one inactive activity, activity 4)", fg="red",),
    ]


def test_alias_search_project(cli, alias_config):
    output = cli('alias', ['list', '-r', '43'])
    lines = output.splitlines()

    assert lines == [
        "[test] 43/1 -> active1 (active project, activity 1)",
        "[test] 43/2 -> active2 (active project, activity 2)",
    ]


def test_alias_no_results(cli, alias_config):
    output = cli('alias', ['list', '12'])
    lines = output.splitlines()

    assert len(lines) == 0


def test_alias_search_project_activity(cli, alias_config):
    output = cli('alias', ['list', '-r', '43/1'])
    lines = output.splitlines()
    assert lines == ["[test] 43/1 -> active1 (active project, activity 1)"]


def test_alias_search_project_activity_no_results(cli, alias_config):
    output = cli('alias', ['list', '-r', '43/5'])
    assert not output


def test_alias_add(cli, alias_config):
    cli('alias', ['add', '-b', 'test', 'bar', '43/1'])

    with open(alias_config.path, 'r') as f:
        config_lines = f.readlines()

    assert 'bar = 43/1\n' in config_lines


def test_local_alias(cli, alias_config):
    alias_config.set('local_aliases', '__pingpong', '')
    output = cli('alias', ['list'])
    assert '[local] __pingpong -> not mapped' in output


@freeze_time('2017-06-21')
def test_used_option_only_shows_used_aliases(cli, entries_file, alias_config):
    entries_file.write("""20.06.2017
    active1 1 Play ping-pong
    """)

    output = cli('alias', ['list', '--used'])

    assert 'active2' not in output
    assert 'active1' in output


def test_alias_no_inactive_excludes_inactive_aliases(cli, alias_config):
    stdout = cli('alias', ['list', '--no-inactive'])

    assert 'not started project' not in stdout
    assert 'active project' in stdout


@freeze_time('2017-06-21')
def test_search_string_can_be_used_with_used_flag(cli, entries_file, alias_config):
    entries_file.write("""20.06.2017
    p2_active 1 Play ping-pong
    active2 1 Play ping-pong
    """)

    stdout = cli('alias', ['list', '--used', 'active2'])

    assert 'active2' in stdout
    assert 'p2_active' not in stdout


@freeze_time('2017-06-21')
def test_no_inactive_flag_can_be_used_with_used_flag(cli, entries_file, alias_config):
    entries_file.write("""20.06.2017
    inactive1 1 Play ping-pong
    active2 1 Play ping-pong
    """)

    stdout = cli('alias', ['list', '--used', '--no-inactive'])

    assert 'inactive1' not in stdout
    assert 'active2' in stdout


@freeze_time('2017-06-21')
def test_used_flag_includes_inactive_by_default(cli, entries_file, alias_config):
    entries_file.write("""20.06.2017
    inactive1 1 Play ping-pong
    """)

    stdout = cli('alias', ['list', '--used'])

    assert 'inactive1' in stdout
