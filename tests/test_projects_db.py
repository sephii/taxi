from __future__ import unicode_literals

import pickle
import pytest

from taxi import projects


def test_legacy_projects_db(tmpdir):
    projects_db_file = tmpdir.join('projects_db')

    local_projects_db = projects.LocalProjectsDb()
    foo = pickle.dumps(local_projects_db)

    with projects_db_file.open(mode='wb') as f:
        f.write(foo)

    p = projects.ProjectsDb(projects_db_file.strpath)
    with pytest.raises(projects.OutdatedProjectsDbException):
        p.get_projects()


def test_outdated_projects_db(tmpdir):
    projects_db_file = tmpdir.join('projects_db')

    # Simulate a projects db version change
    projects.LocalProjectsDb.VERSION = 1
    try:
        p = projects.ProjectsDb(projects_db_file.strpath)
        p.update([])
    finally:
        projects.LocalProjectsDb.VERSION = 2

    with pytest.raises(projects.OutdatedProjectsDbException):
        p.get_projects()
