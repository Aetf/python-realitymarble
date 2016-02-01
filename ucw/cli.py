import click
from ucw.realitymarble import RealityMarble


@click.command()
@click.option('--reality-marble', '-r', help='Path to your reality marble',
              default='~/customizations', type=click.Path(
              file_okay=False, writable=True, resolve_path=False))
@click.argument('name', default='world', required=False)
def main(name, reality_marble):
    """
    Collect configuration files into your own reality marble
    and recreate your system by projecting them on top of an existing system.
    """
    marble = RealityMarble(reality_marble)
    click.echo('{0}, {1}, {2}.'.format(marble.path, marble.etc, marble.home))
