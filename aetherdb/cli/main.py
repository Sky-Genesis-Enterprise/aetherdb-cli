import click
from .shell import launch_shell
from .connection import (
    get_connection, list_profiles, create_or_update_profile, remove_profile
)
from .config import get_profile

@click.group()
def cli():
    """AetherDB CLI: Universal command-line tool for AetherDB databases"""
    pass

@cli.command()
@click.option('--profile', default=None, help="Connection profile name")
@click.option('-c', '--command', default=None, help="Run a single SQL command and exit")
def shell(profile, command):
    """Launch interactive shell or run a single SQL command"""
    conn = get_connection(profile)
    if command:
        launch_shell(conn, sql=command, oneshot=True, profile=profile)
    else:
        launch_shell(conn, profile=profile)

@cli.group()
def apm():
    """Interact with Aether Package Manager (APM) to manage extensions/packages"""
    pass

@apm.command('install')
@click.argument('package')
def install(package):
    click.echo(f"[mock] Installing extension {package} via APM...")

@apm.command('remove')
@click.argument('package')
def remove(package):
    click.echo(f"[mock] Removing extension {package} via APM...")

@apm.command('update')
@click.argument('package')
def update(package):
    click.echo(f"[mock] Updating extension {package} via APM...")

@apm.command('list')
def list_packages():
    click.echo(f"[mock] Listing AetherDB extensions via APM...")

@cli.group()
def profile():
    """Manage connection profiles for AetherDB instances"""
    pass

@profile.command('list')
def list_profiles_cmd():
    click.echo("Available profiles:")
    for p in list_profiles():
        d = get_profile(p)
        click.echo(f"  {p}: {d['user']}@{d['host']}:{d['port']} [{d['database']}]")

@profile.command('create')
@click.argument('name')
@click.option('--host', prompt=True)
@click.option('--port', prompt=True, type=int)
@click.option('--user', prompt=True)
@click.option('--database', prompt=True)
def create_profile(name, host, port, user, database):
    create_or_update_profile(name, host, port, user, database)
    click.echo(f"Profile '{name}' saved.")

@profile.command('remove')
@click.argument('name')
def remove_profile_cmd(name):
    if remove_profile(name):
        click.echo(f"Profile '{name}' removed.")
    else:
        click.echo(f"Profile '{name}' not found.")

if __name__ == "__main__":
    cli()
