from freezegun import freeze_time

from . import CommandTestCase


@freeze_time('2014-01-20')
class StatusCommandTestCase(CommandTestCase):
    def test_local_alias(self):
        config = self.default_config.copy()
        config['default']['local_aliases'] = '_pingpong'

        self.write_entries("""20/01/2014
_pingpong 0800-0900 Play ping-pong
""")
        stdout = self.run_command('status', options=self.default_options)

        self.assertIn(
            "_pingpong (local)              1.00  Play ping-pong",
            stdout
        )

    def test_multiple_local_aliases(self):
        config = self.default_config.copy()
        config['default']['local_aliases'] = '_pingpong, _coffee'

        self.write_entries("""20/01/2014
_pingpong 0800-0900 Play ping-pong
_coffee 0900-1000 Drink some coffee
""")

        stdout = self.run_command('status', options=self.default_options)
        self.assertIn(
            "_pingpong (local)              1.00  Play ping-pong",
            stdout
        )
        self.assertIn(
            "_coffee (local)                1.00  Drink some coffee",
            stdout
        )
