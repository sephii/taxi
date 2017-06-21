from __future__ import unicode_literals

import json
import pkg_resources
import subprocess
import sys

import click
from six.moves.urllib import request
from six.moves.urllib.error import HTTPError

from .base import cli
from ..plugins import plugins_registry
from ..ui import echo_error, echo_success


def run_command(command):
    """
    Run the given command which should be a list like `subprocess.Popen`
    expects. stdout is captured and returned by this function. If the command
    exit code is not 0, `subprocess.CalledProcessError` will be raised.
    """
    return subprocess.check_output(command)


def get_plugin_info(plugin):
    """
    Fetch information about the given package on PyPI and return it as a dict.
    If the package cannot be found on PyPI, :exc:`NameError` will be raised.
    """
    url = 'https://pypi.python.org/pypi/{}/json'.format(plugin)

    try:
        resp = request.urlopen(url)
    except HTTPError as e:
        if e.code == 404:
            raise NameError("Plugin {} could not be found.".format(plugin))
        else:
            raise ValueError(
                "Checking plugin status on {} returned HTTP code {}".format(
                    url, resp.getcode()
                )
            )

    try:
        json_resp = json.loads(resp.read().decode())
    # Catch ValueError instead of JSONDecodeError which is only available in
    # Python 3.5+
    except ValueError:
        raise ValueError(
            "Could not decode JSON info for plugin at {}".format(url)
        )

    return json_resp['info']


def get_installed_plugins():
    """
    Return a dict {plugin_name: version} of installed plugins.
    """
    return {
        # Strip the first five characters from the plugin name since all
        # plugins are expected to start with `taxi-`
        backend.dist.project_name[5:]: backend.dist.version
        for backend in backends_registry._entry_points.values()
        if backend.dist.project_name != 'taxi'
    }


def get_plugin_name(plugin):
    """
    Return the PyPI name of the given plugin.
    """
    return 'taxi-' + plugin


def ensure_inside_venv(ctx):
    """
    Display an error and exit if the program is not run from inside a
    virtualenv.
    """
    if not hasattr(sys, 'real_prefix'):
        echo_error("You're not supposed to use the plugin commands with a "
                   "system-wide install of Taxi. Please install the specific "
                   "packages for your operating system instead.")
        sys.exit(2)


@cli.group()
@click.pass_context
def plugin(ctx):
    pass


@plugin.command(name='list')
@click.pass_context
def list_(ctx):
    """
    Lists installed plugins.
    """
    plugins = plugins_registry.get_plugins()

    click.echo("\n".join(
        ["%s (%s)" % p for p in plugins.items()]
    ))


@plugin.command()
@click.argument('plugin', required=True)
@click.pass_context
def install(ctx, plugin):
    """
    Install the given plugin.
    """
    ensure_inside_venv(ctx)

    plugin_name = get_plugin_name(plugin)
    try:
        info = get_plugin_info(plugin_name)
    except NameError:
        echo_error("Plugin {} could not be found.".format(plugin))
        sys.exit(1)
    except ValueError as e:
        echo_error("Unable to retrieve plugin info. "
                   "Error was:\n\n {}".format(e))
        sys.exit(1)

    try:
        installed_version = pkg_resources.get_distribution(plugin_name).version
    except pkg_resources.DistributionNotFound:
        installed_version = None

    if installed_version is not None and info['version'] == installed_version:
        click.echo("You already have the latest version of {} ({}).".format(
            plugin, info['version']
        ))
        return

    pinned_plugin = '{0}=={1}'.format(plugin_name, info['version'])
    try:
        run_command([sys.executable, '-m', 'pip', 'install', pinned_plugin])
    except subprocess.CalledProcessError as e:
        echo_error("Error when trying to install plugin {}. "
                   "Error was:\n\n {}".format(plugin, e))
        sys.exit(1)

    echo_success("Plugin {} {} installed successfully.".format(
        plugin, info['version']
    ))


@plugin.command()
@click.argument('plugin', required=True)
@click.pass_context
def uninstall(ctx, plugin):
    """
    Uninstall the given plugin.
    """
    ensure_inside_venv(ctx)

    if plugin not in get_installed_plugins():
        echo_error("Plugin {} does not seem to be installed.".format(plugin))
        sys.exit(1)

    plugin_name = get_plugin_name(plugin)
    try:
        run_command([sys.executable, '-m', 'pip', 'uninstall', '-y',
                     plugin_name])
    except subprocess.CalledProcessError as e:
        echo_error(
            "Error when trying to uninstall plugin {}. Error message "
            "was:\n\n{}".format(plugin, e.output.decode())
        )
        sys.exit(1)
    else:
        echo_success("Plugin {} uninstalled successfully.".format(plugin))
