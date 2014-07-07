import os
import shutil
import tempfile
import datetime

from freezegun import freeze_time

from . import CommandTestCase


@freeze_time('2014-01-21')
class StatusCommandTestCase(CommandTestCase):
    def test_status_previous_file(self):
        tmp_entries_dir = tempfile.mkdtemp()
        config = self.default_config.copy()

        os.remove(self.entries_file)

        self.entries_file = os.path.join(tmp_entries_dir, '%m_%Y.txt')
        config['default']['file'] = self.entries_file

        freeze_time('2014-01-21')

        self.write_entries("""17/01/2014
alias_1 2 foobar
""")

        with freeze_time('2014-02-05'):
            self.write_entries("""05/02/2014
    alias_1 4 foobar
    """)

            options = self.default_options.copy()
            options['ignore_date_error'] = True

            stdout = self.run_command('status', config_options=config,
                    options=options)
        shutil.rmtree(tmp_entries_dir)
