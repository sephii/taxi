from __future__ import unicode_literals

from freezegun import freeze_time

from taxi.projects import Activity, Project, ProjectsDb
from taxi.settings import Settings

from . import CommandTestCase, override_settings


class CleanAliasesCommandTestCase(CommandTestCase):
    @override_settings({'test_aliases': {
        'alias_not_started': '0/0',
        'alias_active': '1/0',
        'alias_finished': '2/0',
        'alias_cancelled': '3/0',
    }})
    @freeze_time('2014-01-21')
    def test_project_status(self):
        projects_db = ProjectsDb(self.taxi_dir)

        project_not_started = Project(0, 'not started project',
                                      Project.STATUS_NOT_STARTED)
        project_not_started.backend = 'test'
        project_not_started.activities.append(Activity(0, 'activity', 0))
        project_active = Project(1, 'active project', Project.STATUS_ACTIVE)
        project_active.backend = 'test'
        project_active.activities.append(Activity(0, 'activity', 0))
        project_finished = Project(2, 'finished project',
                                   Project.STATUS_FINISHED)
        project_finished.backend = 'test'
        project_finished.activities.append(Activity(0, 'activity', 0))
        project_cancelled = Project(3, 'cancelled project',
                                    Project.STATUS_CANCELLED)
        project_cancelled.backend = 'test'
        project_cancelled.activities.append(Activity(0, 'activity', 0))
        projects_db.update([
            project_not_started, project_active, project_finished,
            project_cancelled
        ])

        self.run_command('clean-aliases', args=['--yes'])

        settings = Settings(self.config_file)
        self.assertEqual(list(settings.get_aliases().keys()), ['alias_active'])
