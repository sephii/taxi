import os
import shutil
import tempfile

from freezegun import freeze_time

from . import CommandTestCase


class StatusCommandTestCase(CommandTestCase):
    def test_status_previous_file(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        with freeze_time('2014-01-01'):
            self.write_entries("""01/01/2014
alias_1 1 january
""")

        with freeze_time('2014-02-01'):
            self.write_entries("""01/02/2014
    alias_1 1 february
    """)

            options = self.default_options.copy()
            options['ignore_date_error'] = True

            stdout = self.run_command('status', config_options=config,
                                      options=options)
        shutil.rmtree(tmp_entries_dir)

        self.assertIn('january', stdout)
        self.assertIn('february', stdout)
