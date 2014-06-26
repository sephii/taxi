import tempfile

from freezegun import freeze_time

from taxi.models import Project, Activity
from taxi.projectsdb import ProjectsDb
from taxi.settings import Settings

from . import CommandTestCase


@freeze_time('2014-01-21')
class EditCommandTestCase(CommandTestCase):
    def test_autofill_with_specified_file(self):
        """
        Edit with specified date should not autofill it.
        """
        config = self.default_config.copy()
        options = self.default_options.copy()

        config['default']['auto_fill_days'] = '0,1,2,3,4,5,6'
        options['file'] = self.entries_file

        self.run_command('edit')

        with open(self.entries_file, 'r') as f:
            self.assertEqual(f.read(), '')
