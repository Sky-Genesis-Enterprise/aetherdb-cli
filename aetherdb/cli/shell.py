from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
import getpass
from tabulate import tabulate
import os
import json
import csv
import sys
from aetherdb.db_engine import AetherDB
from ..cli.config import get_profile, save_profiles, load_profiles
from ..cli.connection import get_connection, list_profiles, get_profile
from ..cli.apm_integration import apm_install, apm_remove, apm_update, apm_list
from rich.console import Console
from rich.text import Text
from rich.table import Table

SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "VALUES", "SET", "CREATE", "TABLE",
    "ALTER", "ADD", "RENAME", "DROP", "GRANT", "REVOKE", "USE", "SHOW", "PROFILE", "CONNECT"
]
META_COMMANDS = ["\\q", "\\help", "\\profiles", "\\apm", "\\log", "\\login"]
HIST_FILE = os.path.expanduser("~/.aetherdb_cli_history")

FORMATS = ["table", "csv", "json", "raw"]

console = Console()

META_DOCS = {
    "\\help, \\?": "Show this help legend or help for \\help <command>",
    "\\profiles": "List available connection profiles",
    "\\connect <name>": "Reconnect using the given saved profile",
    "\\set format <mode>": f"Change output format (modes: table, csv, json, raw)",
    "\\saveprofile <name>": "Save current session state as a connection profile",
    "\\login": "Re-enter your password and (re)authenticate",
    "\\format <mode>": "Shortcut to change output format",
    "\\i <file>": "Execute SQL/meta-commands from a file (scripting)",
    "\\apm <cmd>": "Run APM extension commands (install, list, etc)",
    "\\migrate, \\rollback": "Run or revert database migrations (stub)",
    "\\q, exit, quit": "Exit AetherDB",
}

def _get_schema_words(db):
    words = set(SQL_KEYWORDS + META_COMMANDS)
    try:
        for tname, table in db.tables.items():
            words.add(tname)
            words.update(table.schema.keys())
    except Exception:
        pass
    return list(words)

def _render_result(result, fmt):
    if result is None:
        console.print("[green]OK[/green]")
        return
    if isinstance(result, list):
        if not result:
            console.print("[yellow](no rows)[/yellow]")
            return
        if fmt == "table":
            print(tabulate(result, headers="keys"))
        elif fmt == "json":
            console.print_json(json.dumps(result, indent=2))
        elif fmt == "csv":
            writer = csv.DictWriter(sys.stdout, fieldnames=result[0].keys())
            writer.writeheader()
            writer.writerows(result)
        elif fmt == "raw":
            for row in result:
                print(row)
        else:
            console.print("[red][Unknown format, showing as table][/red]")
            print(tabulate(result, headers="keys"))
    else:
        console.print(f"[cyan]{result}[/cyan]")

class SessionState:
    def __init__(self, profile_name, profile_conf, user, output_format="table"):
        self.profile_name = profile_name
        self.profile_conf = profile_conf
        self.user = user
        self.output_format = output_format
    def as_profile(self):
        d = dict(self.profile_conf)
        d['user'] = self.user
        return d

def launch_shell(connection, sql=None, oneshot=False, profile=None):
    # Try to get user/pass, prompt if needed
    profile_conf = get_profile(profile)
    db = AetherDB()
    user = profile_conf.get('user', 'aether')
    state = SessionState(profile, profile_conf, user, "table")
    # Authentication flow
    auth_ok = False
    password = None
    for _ in range(3):
        password = getpass.getpass(f"Password for {user}: ")
        if db.login(user, password):
            console.print(f"[green]Authenticated as: {user}[/green]")
            auth_ok = True
            break
        else:
            console.print("[red]Authentication failed. Try again.[/red]")
    if not auth_ok:
        console.print("[red]Could not authenticate with AetherDB engine. Exiting shell.[/red]")
        return
    console.print(f"[green]Connected to: {connection}[/green]")
    if oneshot and sql:
        console.print(f"SQL> {sql}")
        # TODO: actually execute sql: result = db.execute_sql(sql)
        console.print("[mock] Would execute query and print result")
        return
    prompt_str = f"aetherdb[{connection}]> "

    # Build initial completion set
    def refresh_completer():
        return WordCompleter(_get_schema_words(db), ignore_case=True)

    completer = refresh_completer()
    session = PromptSession(history=FileHistory(HIST_FILE), completer=completer)

    while True:
        try:
            session.completer = refresh_completer()  # Always refresh for live DDL
            cmd = session.prompt(prompt_str)
            if not cmd.strip():
                continue
            if cmd.strip().lower() in ("\\q", "exit", "quit"):
                console.print('[green]Bye.[/green]')
                break
            if cmd.startswith('\\'):
                # Help docs legend
                if cmd.strip() in ["\\help", "\\?", "help"] or cmd.strip().startswith("\\help"):
                    arg = cmd.strip().split()[1:] if len(cmd.strip().split()) > 1 else None
                    if not arg:
                        table = Table(title="AetherDB Meta-Commands", box=None, show_lines=False)
                        table.add_column("Meta-command", style="cyan bold")
                        table.add_column("Usage/Description", style="yellow")
                        for k, v in META_DOCS.items():
                            table.add_row(k, v)
                        console.print(table)
                    else:
                        lookup = arg[0]
                        for k in META_DOCS:
                            if lookup in k:
                                console.print(f"[cyan]{k}[/cyan]: {META_DOCS[k]}")
                                break
                        else:
                            console.print(f"[red]No help for: {lookup}[/red]")
                    continue
                # Profiles and reconnecting
                if cmd.strip() == "\\profiles":
                    console.print("[bold]Available profiles:[/bold]")
                    for pname in list_profiles():
                        p = get_profile(pname)
                        highlight = "*" if pname == state.profile_name else " "
                        console.print(f"{highlight} [cyan]{pname}[/cyan]: {p['user']}@{p['host']}:{p['port']} [{p['database']}] ")
                    continue
                if cmd.strip().startswith("\\connect"):
                    parts = cmd.strip().split()
                    if len(parts) == 2:
                        newprof = parts[1]
                        if newprof in list_profiles():
                            console.print(f"[yellow]Switching to profile {newprof}. Please re-authenticate...[/yellow]")
                            # Reenter shell with new profile and user/pass
                            launch_shell(get_connection(newprof), profile=newprof)
                            return  # terminate this session, replaced by new one
                        else:
                            console.print(f"[red]Profile '{newprof}' not found.[/red]")
                    else:
                        console.print("[yellow]Usage: \\connect <profile>[/yellow]")
                    continue
                # File include
                if cmd.strip().startswith("\\i"):
                    parts = cmd.strip().split()
                    if len(parts) == 2:
                        fname = parts[1]
                        if not os.path.exists(fname):
                            console.print(f"[red]File not found: {fname}[/red]")
                        else:
                            console.print(f"[yellow]Running command file: {fname}[/yellow]")
                            with open(fname) as f:
                                for line in f:
                                    if not line.strip() or line.strip().startswith("--"):  # skip comments
                                        continue
                                    if line.strip().startswith("\\"):
                                        cmd = line.strip()
                                    else: # SQL
                                        cmd = line.strip()
                                    console.print(f"> {cmd}")
                                    # Recursively run meta/sql commands
                                    if cmd.startswith("\\"):
                                        # restarts recursion, but ok for now (shell exit on \\q is fine)
                                        session.default_buffer.insert_text(cmd)
                                    else:
                                        try:
                                            result = db.execute_sql(cmd)
                                            _render_result(result, state.output_format)
                                        except Exception as e:
                                            console.print(Text(f"Error: {e}", style="red"))
                        continue
                    else:
                        console.print("[yellow]Usage: \\i <filename>[/yellow]")
                    continue
                # APM commands
                if cmd.strip().startswith("\\apm"):
                    parts = cmd.strip().split()
                    if len(parts) >= 2:
                        op = parts[1]
                        if op == "install" and len(parts) == 3:
                            result = apm_install(parts[2])
                            console.print(f"[green]{result}[/green]")
                        elif op == "remove" and len(parts) == 3:
                            result = apm_remove(parts[2])
                            console.print(f"[green]{result}[/green]")
                        elif op == "update" and len(parts) == 3:
                            result = apm_update(parts[2])
                            console.print(f"[green]{result}[/green]")
                        elif op == "list":
                            exts = apm_list()
                            table = Table(title="Installed Extensions", box=None)
                            table.add_column("Extension", style="yellow")
                            for e in exts:
                                table.add_row(e)
                            console.print(table)
                        else:
                            console.print("[yellow]Usage: \\apm <install|remove|update|list> [extension][/yellow]")
                    else:
                        console.print("[yellow]Usage: \\apm <install|remove|update|list> [extension][/yellow]")
                    continue
                # Migration stubs
                if cmd.strip().startswith("\\migrate"):
                    console.print("[green][stub] Migrations applied successfully![/green]")
                    continue
                if cmd.strip().startswith("\\rollback"):
                    console.print("[yellow][stub] Rolled back one migration.[/yellow]")
                    continue
                # New: \set <key> <value>
                if cmd.strip().startswith("\\set"):
                    parts = cmd.strip().split()
                    if len(parts) == 3 and parts[1].lower() == "format" and parts[2] in FORMATS:
                        state.output_format = output_format = parts[2]
                        console.print(f"[green][output format now: {output_format}][/green]")
                    else:
                        console.print(f"[yellow]Usage: \\set format [{'|'.join(FORMATS)}][/yellow]")
                    continue
                # New: \saveprofile <name>
                if cmd.strip().startswith("\\saveprofile"):
                    parts = cmd.strip().split()
                    if len(parts) == 2:
                        name = parts[1]
                        profiles = load_profiles()
                        profiles[name] = state.as_profile()
                        save_profiles(profiles)
                        console.print(f"[green]Profile '{name}' saved.[/green]")
                    else:
                        console.print("[yellow]Usage: \\saveprofile <name>[/yellow]")
                    continue
                # ...existing \login and else meta handler...
                if cmd.strip() == "\\login":
                    for _ in range(3):
                        password = getpass.getpass(f"Password for {user}: ")
                        if db.login(user, password):
                            state.user = user
                            console.print(f"[green]Authenticated as: {user}[/green]")
                            break
                        else:
                            console.print("[red]Authentication failed. Try again.[/red]")
                    continue
                console.print(f"[blue][meta] Would run meta-command: {cmd}[/blue]")
            else:
                try:
                    result = db.execute_sql(cmd)
                    _render_result(result, state.output_format)
                except PermissionError as e:
                    console.print(Text(str(e), style="yellow"))
                    console.print("[red]Hint: Check your login, role, or GRANT/REVOKE permissions.[/red]")
                except ValueError as e:
                    console.print(Text(str(e), style="red bold"))
                    if "parse" in str(e).lower() or "syntax" in str(e).lower():
                        console.print("[yellow]Hint: Check your SQL syntax.[/yellow]")
                except Exception as e:
                    console.print(Text(f"Unexpected error: {e}", style="red"))
        except (EOFError, KeyboardInterrupt):
            console.print('[green]Bye.[/green]')
            break
