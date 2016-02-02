import click
import json

from ucw.realitymarble import RealityMarble
from ucw.utils import sudo, class_by_name


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--reality-marble', '-r',
              help='Path to your reality marble, can also be specified by env variable REALITY_MARBLE',
              default='~/customizations', envvar='REALITY_MARBLE',
              type=click.Path(file_okay=False, writable=True, resolve_path=False))
@click.option('--debug', '-d', is_flag=True,
              help='Enable debug output')
def main(ctx, reality_marble, debug):
    """
    Manage configuration files in your own reality marble
    and recreate your system by projecting them on top of an existing system.
    """
    marble = RealityMarble(reality_marble)
    if not ctx.obj:
        ctx.obj = {}
    ctx.obj['marble'] = marble
    if debug:
        marble.dump_config()


@main.command()
@click.pass_context
@click.argument('files', nargs=-1, type=click.Path(dir_okay=False))
def collect(ctx, files):
    """
    Collect FILES into your reality marble.
    """
    for f in files:
        ctx.obj['marble'].collect(f)


@main.command(name='sudohelper')
@click.pass_context
@click.argument('method', required=True)
@click.argument('args')
def sudo_helper(ctx, method, args):
    argv = json.loads(args)
    res = class_by_name(method)(*argv)
    click.echo(json.dumps(res))
