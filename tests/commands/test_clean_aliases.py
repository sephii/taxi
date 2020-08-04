from freezegun import freeze_time

from taxi.projects import Activity, Project, ProjectsDb
from taxi.settings import Settings


@freeze_time('2014-01-21')
def test_project_status(cli, config, data_dir):
    config.set_dict({
        'test_aliases': {
            'alias_not_started': '0/0',
            'alias_active': '1/0',
            'alias_finished': '2/0',
            'alias_cancelled': '3/0',
        }
    })
    projects_db = ProjectsDb(str(data_dir))

    project_not_started = Project(0, 'not started project',
                                  Project.STATUS_NOT_STARTED)
    project_not_started.backend = 'test'
    project_not_started.activities.append(Activity(0, 'activity'))
    project_active = Project(1, 'active project', Project.STATUS_ACTIVE)
    project_active.backend = 'test'
    project_active.activities.append(Activity(0, 'activity'))
    project_finished = Project(2, 'finished project',
                               Project.STATUS_FINISHED)
    project_finished.backend = 'test'
    project_finished.activities.append(Activity(0, 'activity'))
    project_cancelled = Project(3, 'cancelled project',
                                Project.STATUS_CANCELLED)
    project_cancelled.backend = 'test'
    project_cancelled.activities.append(Activity(0, 'activity'))
    projects_db.update([
        project_not_started, project_active, project_finished,
        project_cancelled
    ])

    cli('clean-aliases', ['--yes'])

    settings = Settings(config.path)
    assert list(settings.get_aliases().keys()) == ['alias_active']
