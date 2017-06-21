from __future__ import unicode_literals

import pytest

from taxi.projects import Activity, Project, ProjectsDb


@pytest.fixture
def projects_db(data_dir):
    projects_db = ProjectsDb(str(data_dir))
    projects_list = []

    project = Project(42, 'not started project',
                      Project.STATUS_NOT_STARTED)
    project.backend = 'test'
    projects_list.append(project)

    project = Project(43, 'active project',
                      Project.STATUS_ACTIVE)
    project.backend = 'test'
    project.activities.append(Activity(1, 'activity 1', 0))
    project.activities.append(Activity(2, 'activity 2', 0))
    projects_list.append(project)

    project = Project(44, '2nd active project',
                      Project.STATUS_ACTIVE)
    project.backend = 'test'
    project.activities.append(Activity(1, 'activity 1', 0))
    projects_list.append(project)

    projects_db.update(projects_list)

    return projects_db


def test_no_arguments_lists_projects(cli, projects_db):
    lines = cli('project').splitlines()

    assert set(lines) == set([
        'N [test]   42 not started project',
        'A [test]   43 active project',
        'A [test]   44 2nd active project',
    ])


def test_argument_filters_search(cli, projects_db):
    lines = cli('project', ['list', 'active']).splitlines()

    assert set(lines) == set([
        'A [test]   43 active project',
        'A [test]   44 2nd active project',
    ])


def test_add_creates_alias(cli, config, projects_db):
    cli('project', ['alias', 'active'], input='1\n0\nfoobar')

    with open(config.path, 'r') as f:
        config_lines = f.readlines()

    assert 'foobar = 43/1\n' in config_lines


def test_show_inactive_project_shows_project(cli, projects_db):
    lines = cli('project', ['show', '42']).splitlines()
    assert lines[0] == 'Id: 42'


def test_show_shows_project(cli, projects_db):
    lines = cli('project', ['show', '43']).splitlines()
    assert lines[0] == 'Id: 43'


def test_show_nonexistent_project_shows_error(cli):
    output = cli('project', ['show', '777'])
    assert output == 'Error: Could not find project `777`\n'


def test_add_single_choice(cli, data_dir, config):
    project = Project(1, 'test project', Project.STATUS_ACTIVE)
    project.activities = [Activity(2, 'test activity', 0)]
    p = ProjectsDb(str(data_dir))
    p.update([project])

    cli('project', ['alias', 'test project'], input='test_alias')

    with open(config.path, 'r') as f:
        lines = f.readlines()

    assert 'test_alias = 1/2\n' in lines


def test_add_multiple_choices(cli, data_dir, config):
    p1 = Project(1, 'test project', Project.STATUS_ACTIVE)
    p1.activities = [Activity(2, 'test activity', 0)]
    p2 = Project(2, 'test project 2', Project.STATUS_ACTIVE)
    p2.activities = [Activity(3, 'test activity 2', 0)]
    p = ProjectsDb(str(data_dir))
    p.update([p1, p2])

    cli('project', ['alias', 'test project'], input='1\ntest_alias')

    with open(config.path, 'r') as f:
        lines = f.readlines()

    assert 'test_alias = 2/3\n' in lines

def test_add_inactive_project(cli, data_dir):
    project = Project(1, 'test project', Project.STATUS_FINISHED)
    project.activities = [Activity(2, 'test activity', 0)]
    p = ProjectsDb(str(data_dir))
    p.update([project])

    output = cli('project', ['alias', 'test project'], input='test_alias')

    assert "No active project matches your search string" in output
