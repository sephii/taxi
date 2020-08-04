from unittest.mock import patch


def test_config_works_with_invalid_syntax(cli, config):
    with open(config.path, "w") as fp:
        fp.write("[foobar")

    with patch("taxi.commands.config.click.edit") as edit:
        cli("config")
        edit.assert_called_once_with(filename=config.path)


def test_config_works_with_invalid_value(cli, config):
    config.set("taxi", "auto_fill_days", "foobar")
    with patch("taxi.commands.config.click.edit") as edit:
        cli("config")
        edit.assert_called_once_with(filename=config.path)
