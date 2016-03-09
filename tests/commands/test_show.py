from __future__ import unicode_literals

from taxi.projects import Activity, Project, ProjectsDb

from . import CommandTestCase, override_settings


@override_settings()
class ShowCommandTestCase(CommandTestCase):
    def setUp(self):
        super(ShowCommandTestCase, self).setUp()
        self.projects_db = ProjectsDb(self.taxi_dir)
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
        self.projects_db.update(projects_list)

    def test_show_inexistent_object(self):
        output = self.run_command('show', ['aoeuidhtns'])
        self.assertEqual(output, "Your search string aoeuidhtns is nothing.\n")

    def test_show_project_id(self):
        output = self.run_command('show', ['42'])
        self.assertEqual(output, "Your search string 42 is the project not "
                                 "started project.\n")

    def test_show_activity_id(self):
        output = self.run_command('show', ['42/1'])
        self.assertEqual(output, "Your search string 42/1 is the activity "
                                 "activity 1 of the project not started "
                                 "project.\n")

    def test_show_activity_id_mapped(self):
        output = self.run_command('show', ['123/456'])
        self.assertEqual(output, "Your search string 123/456 is the activity "
                                 "my activity of the project my project, "
                                 "aliased by alias_1 on the test backend.\n")

    def test_show_alias(self):
        output = self.run_command('show', ['alias_1'])
        self.assertEqual(output, "Your search string alias_1 is an alias to "
                                 "my project, my activity (123/456) on the "
                                 "test backend.\n")

    @override_settings({'local_aliases': {
        '__pingpong': None
    }})
    def test_show_local_alias(self):
        output = self.run_command('show', ['__pingpong'])
        self.assertEqual(output, "Your search string __pingpong is a local "
                                 "alias.\n")
