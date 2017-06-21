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
    project.activities.append(Activity(1, 'activity 1', 0))
    project.activities.append(Activity(2, 'activity 2', 0))
    projects_list.append(project)
    project = Project(123, 'my project', Project.STATUS_ACTIVE)
    project.backend = 'test'
    project.activities.append(Activity(456, 'my activity', 0))
    projects_list.append(project)
    projects_db.update(projects_list)

    return projects_db


def test_show_inexistent_object(cli):
    output = cli('show', ['aoeuidhtns'])
    assert output == "Your search string aoeuidhtns is nothing.\n"


def test_show_project_id(cli, projects_db):
    output = cli('show', ['42'])
    assert output == ("Your search string 42 is the project not "
                      "started project.\n")


def test_show_activity_id(cli, projects_db):
    output = cli('show', ['42/1'])
    assert output == ("Your search string 42/1 is the activity "
                      "activity 1 of the project not started "
                      "project.\n")


def test_show_activity_id_mapped(cli, projects_db):
    output = cli('show', ['123/456'])
    assert output == ("Your search string 123/456 is the activity "
                      "my activity of the project my project, "
                      "aliased by alias_1 on the test backend.\n")


def test_show_alias(cli, projects_db):
    output = cli('show', ['alias_1'])
    assert output == ("Your search string alias_1 is an alias to "
                      "my project, my activity (123/456) on the "
                      "test backend.\n")


def test_show_local_alias(cli, config):
    config.set('local_aliases', '__pingpong', '')
    output = cli('show', ['__pingpong'])
    assert output == "Your search string __pingpong is a local alias.\n"
