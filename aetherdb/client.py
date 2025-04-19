"""
AetherDB Client: Interactive CLI (psql-inspired) for running SQL and meta-commands against AetherDB.
"""
import sys
import readline
import getpass
import os
import json
from aetherdb.db_engine import AetherDB
from tabulate import tabulate

SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "VALUES", "SET", "CREATE", "TABLE", "INTO", "ALTER", "ADD", "RENAME", "DROP"
]
META_COMMANDS = ["\\dt", "\\d", "\\du", "\\adduser", "\\login", "\\passwd", "\\whoami", "\\help", "\\q", "\\quit", "\\save", "\\load", "\\grant", "\\revoke", "\\role", "\\log"]

class Completer:
    def __init__(self, client):
        self.client = client
        self.words = set(SQL_KEYWORDS + META_COMMANDS)

    def update_words(self):
        self.words = set(SQL_KEYWORDS + META_COMMANDS)
        self.words.update(self.client.db.tables.keys())
        self.words.update(self.client.db.auth.users.keys())

    def complete(self, text, state):
        self.update_words()
        matches = [w for w in self.words if w.upper().startswith(text.upper())]
        try:
            return matches[state]
        except IndexError:
            return None

class AetherDBClient:
    def __init__(self):
        self.db = AetherDB()
        self.running = True
        self.completer = Completer(self)
        readline.set_completer(self.completer.complete)
        readline.parse_and_bind('tab: complete')
        # Set persistent command history
        self.histfile = os.path.expanduser('~/.aetherdb_history')
        try:
            readline.read_history_file(self.histfile)
        except Exception:
            pass

    def run(self):
        if getattr(self.db, 'bootstrapped_user', False):
            print("*** WARNING: No users found. Bootstrapping with default user 'aether' (no password).\n"
                  "    Please run \\passwd to set a password immediately!\n")
        print(HELP_TEXT)
        while self.running:
            try:
                line = self._read_sql_multiline()
                if not line.strip():
                    continue
                if line.startswith('\\'):
                    self._handle_meta(line.strip())
                else:
                    self._handle_sql(line.strip())
            except (KeyboardInterrupt, EOFError):
                print("\nExiting.")
                break

    def _read_sql_multiline(self):
        lines = []
        prompt = "aetherdb=> "
        while True:
            line = input(prompt if not lines else '... ')
            lines.append(line)
            if line.strip().endswith(';') or line.strip().startswith('\\'):
                break
        return '\n'.join(lines).strip().rstrip(';')

    def _handle_meta(self, cmd):
        import getpass
        if cmd in ("\\q", "\\quit"):
            self.running = False
            print("Bye.")
        elif cmd == "\\passwd":
            pw1 = getpass.getpass("New password: ")
            pw2 = getpass.getpass("Repeat new password: ")
            if pw1 != pw2:
                print("Passwords do not match.")
                return
            try:
                self.db.change_password(pw1)
                print("Password updated for user", self.db.current_user)
            except Exception as e:
                print(f"Set password error: {e}")
        elif cmd == "\\dt":
            if not self.db.current_user:
                print("Error: Please login first.")
            else:
                tables = list(self.db.tables.keys())
                print(tabulate([[t] for t in tables], headers=["Tables"]) if tables else "(no tables)")
        elif cmd == "\\whoami":
            print(f"Current user: {self.db.current_user or '(none)'}")
        elif cmd == "\\adduser":
            username = input("New username: ")
            password = getpass.getpass("New password: ")
            try:
                self.db.add_user(username, password)
                print("User created and logged in as", username)
            except Exception as e:
                print(f"Add user error: {e}")
        elif cmd.startswith("\\login"):
            username = cmd.split(maxsplit=1)[1] if len(cmd.split()) > 1 else input("Username: ")
            password = getpass.getpass(f"Password for {username}: ")
            if self.db.login(username, password):
                print("Logged in as", username)
            else:
                print("Login failed.")
        elif cmd == "\\help":
            print(HELP_TEXT)
        elif cmd.startswith("\\help"):
            arg = cmd[5:].strip().upper() if len(cmd) > 5 else None
            if not arg:
                print(HELP_TEXT)
            elif arg.lstrip('\\').upper() in [c.lstrip('\\').upper() for c in META_COMMANDS]:
                helptexts = {
                    '\\dt': 'Show all tables',
                    '\\d': 'Show schema(s)',
                    '\\du': 'List users and roles',
                    '\\passwd': 'Set your password',
                    '\\login': 'Log in as user',
                    '\\adduser': 'Add a new user and login',
                    '\\save': 'Save encrypted DB',
                    '\\load': 'Load encrypted DB',
                    '\\whoami': 'Print current user',
                    '\\q': 'Quit',
                    '\\grant': 'Grant permission on a table to a user',
                    '\\revoke': 'Revoke permission on a table from a user',
                    '\\role': 'Set user role (admin only): \\role <user> <role>',
                    '\\log': 'Show the audit log: \\log (last 10), \\log N, \\log all',
                }
                print(helptexts.get(arg, f"Meta-command {arg}: no extra help"))
            elif arg in SQL_KEYWORDS:
                sqlhelp = {
                    'SELECT': 'Query table rows',
                    'INSERT': 'Insert a new row',
                    'UPDATE': 'Update existing row',
                    'DELETE': 'Delete row(s)',
                    'ALTER': 'Alter table structure',
                    'RENAME': 'Rename object (table, col)',
                    'CREATE': 'Create table',
                    'DROP': 'Delete table',
                }
                print(sqlhelp.get(arg, f"SQL {arg}: No extra help."))
            else:
                print("Unrecognized command for help.")
        elif cmd == "\\du":
            if not self.db.current_user:
                print("Error: Please login first.")
                return
            print(tabulate([(u, user.role) for u, user in self.db.auth.users.items()], headers=["Username", "Role"]))
        elif cmd.startswith("\\save "):
            if not self.db.current_user:
                print("Error: Please login first.")
                return
            _, path = cmd.split(maxsplit=1)
            pw = getpass.getpass("Encryption password: ")
            try:
                self.db.save_encrypted(path.strip(), pw)
                print(f"Encrypted DB saved to {path.strip()}")
            except Exception as e:
                print(f"Save error: {e}")
        elif cmd.startswith("\\load "):
            if not self.db.current_user:
                print("Error: Please login first.")
                return
            _, path = cmd.split(maxsplit=1)
            pw = getpass.getpass("Decryption password: ")
            try:
                self.db = self.db.load_encrypted(path.strip(), pw)
                print(f"Encrypted DB loaded from {path.strip()}")
            except Exception as e:
                print(f"Load error: {e}")
        elif cmd.startswith("\\d"):
            arg = cmd[2:].strip()
            if not self.db.current_user:
                print("Error: Please login first.")
                return
            if arg:
                # Show schema for one table
                t = self.db.tables.get(arg)
                if not t:
                    print(f"Table '{arg}' not found.")
                else:
                    print(f"Schema for table {arg}:")
                    print(tabulate([[col, t.schema[col]] for col in t.schema], headers=["Column", "Type"]))
                    # Permissions
                    print("Permissions:")
                    print(tabulate([[u, ', '.join(sorted(perms))] for u, perms in t.permissions.items()], headers=["User", "Perms"]))
            else:
                if not self.db.tables:
                    print("No tables.")
                for name, t in self.db.tables.items():
                    print(f"Table: {name}")
                    print(tabulate([[col, t.schema[col]] for col in t.schema], headers=["Column", "Type"]))
                    print("Permissions:")
                    print(tabulate([[u, ', '.join(sorted(perms))] for u, perms in t.permissions.items()], headers=["User", "Perms"]))
        elif cmd.startswith("\\grant"):
            parts = cmd.split()
            if len(parts) != 6 or parts[2] != "on" or parts[4] != "to":
                print("Usage: \\grant <perm> on <table> to <user>")
                return
            perm, table, user = parts[1], parts[3], parts[5]
            try:
                self.db.grant(table, user, perm)
                print(f"Granted {perm} on {table} to {user}")
            except Exception as e:
                print(f"Grant error: {e}")
        elif cmd.startswith("\\revoke"):
            parts = cmd.split()
            if len(parts) != 6 or parts[2] != "on" or parts[4] != "from":
                print("Usage: \\revoke <perm> on <table> from <user>")
                return
            perm, table, user = parts[1], parts[3], parts[5]
            try:
                self.db.revoke(table, user, perm)
                print(f"Revoked {perm} on {table} from {user}")
            except Exception as e:
                print(f"Revoke error: {e}")
        elif cmd.startswith("\\role"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: \\role <user> <role>")
                return
            user, role = parts[1], parts[2]
            try:
                self.db.set_user_role(user, role)
                print(f"Assigned role {role} to user {user}.")
            except Exception as e:
                print(f"Role assignment error: {e}")
        elif cmd.startswith("\\log"):
            parts = cmd.split()
            count = 10
            if len(parts) == 2:
                if parts[1] == "all":
                    count = None
                else:
                    try:
                        count = int(parts[1])
                    except Exception:
                        print("Usage: \\log [N|all]")
                        return
            entries = []
            try:
                with open("aetherdb_audit.log", "r") as f:
                    entries = [json.loads(line) for line in f]
            except FileNotFoundError:
                print("No audit log found.")
                return
            if count:
                entries = entries[-count:]
            if not entries:
                print("(no entries)")
                return
            print(tabulate([[e['ts'], e['user'], e['action'], e.get('detail','')] for e in entries], headers=["Time", "User", "Action", "Detail"]))
        else:
            print(f"Unknown command: {cmd}")

    def _handle_sql(self, sql):
        try:
            result = self.db.execute_sql(sql)
            if result is None:
                print("OK")
            elif isinstance(result, list):
                if result:
                    print(tabulate(result, headers="keys"))
                else:
                    print("(no rows)")
            else:
                print(result)
        except PermissionError as pe:
            print(f"Auth Error: {pe}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    client = AetherDBClient()
    client.run()
