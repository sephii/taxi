from __future__ import unicode_literals

import json
import subprocess
import sys

import click
from six.moves.urllib import request

from .base import cli
from ..backends.registry import backends_registry


def get_plugin_info(plugin):
    # TODO check on Python 2 (read() returns bytes on py3)
    url = 'https://pypi.python.org/pypi/{}/json'.format(plugin)
    resp = request.urlopen(url)

    if resp.getcode() != 200:
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
    plugins = set([
        backend.dist for backend in backends_registry._entry_points.values()
        if backend.dist.project_name != 'taxi'
    ])

    click.echo("\n".join(
        ["%s (%s)" % (p.project_name, p.version) for p in plugins]
    ))


@plugin.command()
@click.argument('plugin', required=True)
@click.pass_context
def install(ctx, plugin):
    """
    Install given plugin.
    """
    import pkg_resources
    ensure_inside_venv(ctx)
    info = get_plugin_info(plugin)
    if info['version'] == pkg_resources.get_distribution(plugin).version:
        click.echo("You already have the latest version")
        return

    pinned_plugin = '{0}=={1}'.format(plugin, info['version'])
    subprocess.call([sys.executable, '-m', 'pip', 'install', pinned_plugin])


@plugin.command()
@click.argument('plugin', required=True)
@click.pass_context
def uninstall(ctx, plugin):
    """
    Uninstall given plugin.
    """
    ensure_inside_venv(ctx)
    subprocess.call([sys.executable, '-m', 'pip', 'uninstall', '-y', plugin])


def ensure_inside_venv(ctx):
    if not hasattr(sys, 'real_prefix'):
        click.secho("You're not supposed to use the plugin commands with a "
                    "system-wide install of Taxi. Please install the specific "
                    "packages for your operating system.", fg='red')

        sys.exit(2)
