import click
import logging

from realitymarble import RealityMarble


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
    logging.basicConfig(level=logging.WARNING,
                        format='%(name)10s - %(funcName)-18s - [%(levelname)5s]: %(message)s')

    marble = RealityMarble(reality_marble)
    if not ctx.obj:
        ctx.obj = {}
    ctx.obj['marble'] = marble
    if debug:
        logging.getLogger().setLevel(logging.NOTSET)
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


@main.command()
@click.pass_context
@click.argument('files', nargs=-1, type=click.Path(dir_okay=False))
def drop(ctx, files):
    """
    Drop FILES from your reality marble, and do not manage them anymore.
    """
    for f in files:
        ctx.obj['marble'].drop(f)


@main.command()
@click.pass_context
@click.argument('files', nargs=-1, type=click.Path(dir_okay=False))
def project(ctx, files):
    """
    Project corresponding file in your reality marble onto FILES.
    """
    for f in files:
        ctx.obj['marble'].project(f)


@main.command()
@click.pass_context
@click.argument('files', nargs=-1, type=click.Path(dir_okay=False))
def materialize(ctx, files):
    """
    Don't manage FILES anymore.
    """
    for f in files:
        ctx.obj['marble'].materialize(f)


@main.command()
@click.pass_context
@click.argument('files', nargs=-1, type=click.Path(dir_okay=False))
def touch(ctx, files):
    """
    Create new configuration files managed by reality marble.
    """
    for f in files:
        ctx.obj['marble'].touch(f)
