from __future__ import unicode_literals

from taxi.projects import Activity, Project, ProjectsDb

from . import CommandTestCase


class AddCommandTestCase(CommandTestCase):
    def test_add_single_choice(self):
        project = Project(1, 'test project', Project.STATUS_ACTIVE)
        project.activities = [Activity(2, 'test activity', 0)]
        p = ProjectsDb(self.taxi_dir)
        p.update([project])

        self.run_command('add', ['test project'], input='test_alias')

        with open(self.config_file, 'r') as f:
            self.assertIn('test_alias = 1/2\n', f.readlines())

    def test_add_multiple_choices(self):
        p1 = Project(1, 'test project', Project.STATUS_ACTIVE)
        p1.activities = [Activity(2, 'test activity', 0)]
        p2 = Project(2, 'test project 2', Project.STATUS_ACTIVE)
        p2.activities = [Activity(3, 'test activity 2', 0)]
        p = ProjectsDb(self.taxi_dir)
        p.update([p1, p2])

        self.run_command('add', ['test project'], input='1\ntest_alias')

        with open(self.config_file, 'r') as f:
            self.assertIn('test_alias = 2/3\n', f.readlines())

    def test_add_inactive_project(self):
        project = Project(1, 'test project', Project.STATUS_FINISHED)
        project.activities = [Activity(2, 'test activity', 0)]
        p = ProjectsDb(self.taxi_dir)
        p.update([project])

        output = self.run_command('add', ['test project'], input='test_alias')

        self.assertIn("No active project matches your search string", output)
