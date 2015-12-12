from __future__ import unicode_literals

from taxi.projects import Activity, Project, ProjectsDb

from . import CommandTestCase, override_settings


@override_settings()
class ProjectCommandTestCase(CommandTestCase):
    def setUp(self):
        super(ProjectCommandTestCase, self).setUp()
        self.projects_db = ProjectsDb(self.taxi_dir)
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

        self.projects_db.update(projects_list)

    def run_project_command(self, *args, **kwargs):
        return self.run_command('project', *args, **kwargs)

    def test_no_arguments_lists_projects(self):
        output = self.run_project_command([])
        lines = output.splitlines()

        self.assertEqual(set(lines), set([
            'N [test]   42 not started project',
            'A [test]   43 active project',
            'A [test]   44 2nd active project',
        ]))

    def test_argument_filters_search(self):
        output = self.run_project_command(['list', 'active'])
        lines = output.splitlines()

        self.assertEqual(set(lines), set([
            'A [test]   43 active project',
            'A [test]   44 2nd active project',
        ]))

    def test_add_creates_alias(self):
        self.run_command('project', ['alias', 'active'],
                         input='1\n0\nfoobar')

        with open(self.config_file, 'r') as f:
            config_lines = f.readlines()

        self.assertIn('foobar = 43/1\n', config_lines)

    def test_show_inactive_project_shows_project(self):
        output = self.run_command('project', ['show', '42'])
        lines = output.splitlines()
        self.assertEqual(lines[0], 'Id: 42')

    def test_show_shows_project(self):
        output = self.run_command('project', ['show', '43'])
        lines = output.splitlines()
        self.assertEqual(lines[0], 'Id: 43')

    def test_show_nonexistent_project_shows_error(self):
        output = self.run_command('project', ['show', '777'])
        self.assertEqual(output, 'Error: Could not find project `777`\n')

    def test_add_single_choice(self):
        project = Project(1, 'test project', Project.STATUS_ACTIVE)
        project.activities = [Activity(2, 'test activity', 0)]
        p = ProjectsDb(self.taxi_dir)
        p.update([project])

        self.run_project_command(['alias', 'test project'], input='test_alias')

        with open(self.config_file, 'r') as f:
            self.assertIn('test_alias = 1/2\n', f.readlines())

    def test_add_multiple_choices(self):
        p1 = Project(1, 'test project', Project.STATUS_ACTIVE)
        p1.activities = [Activity(2, 'test activity', 0)]
        p2 = Project(2, 'test project 2', Project.STATUS_ACTIVE)
        p2.activities = [Activity(3, 'test activity 2', 0)]
        p = ProjectsDb(self.taxi_dir)
        p.update([p1, p2])

        self.run_project_command(['alias', 'test project'],
                                 input='1\ntest_alias')

        with open(self.config_file, 'r') as f:
            self.assertIn('test_alias = 2/3\n', f.readlines())

    def test_add_inactive_project(self):
        project = Project(1, 'test project', Project.STATUS_FINISHED)
        project.activities = [Activity(2, 'test activity', 0)]
        p = ProjectsDb(self.taxi_dir)
        p.update([project])

        output = self.run_project_command(['alias', 'test project'],
                                          input='test_alias')

        self.assertIn("No active project matches your search string", output)
