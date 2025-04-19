"""
Core engine for AetherDB: in-memory table storage, basic CRUD operations, and type enforcement.
"""
from typing import Any, Dict, List, Optional
import datetime

class Table:
    """
    Simple in-memory table supporting rows as dicts, basic data types, and CRUD.
    """
    def __init__(self, name: str, schema: Dict[str, str], creator: str = None):
        self.name = name
        self.schema = schema  # e.g. {"id": "int", "name": "str", ...}
        self.rows: List[Dict[str, Any]] = []
        self.auto_inc = 1  # for autoincrement primary key if needed
        self.permissions = {}  # username -> set('read', 'write', 'admin')
        if creator:
            self.permissions[creator] = {'read', 'write', 'admin'}

    def has_perm(self, user: str, perm: str) -> bool:
        return user in self.permissions and (perm in self.permissions[user] or 'admin' in self.permissions[user])

    def grant(self, user: str, perm: str):
        self.permissions.setdefault(user, set()).add(perm)

    def revoke(self, user: str, perm: str):
        if user in self.permissions and perm in self.permissions[user]:
            self.permissions[user].remove(perm)
        if user in self.permissions and not self.permissions[user]:
            del self.permissions[user]

    def insert(self, row_data: Dict[str, Any]) -> None:
        validated = self._validate_row(row_data)
        self.rows.append(validated)

    def select(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not filters:
            return list(self.rows)
        result = []
        for row in self.rows:
            ok = True
            for k, v in filters.items():
                if row.get(k) != v:
                    ok = False
                    break
            if ok:
                result.append(row)
        return result

    def update(self, filters: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        count = 0
        for row in self.rows:
            if all(row.get(k) == v for k, v in filters.items()):
                for uk, uv in update_data.items():
                    if uk in self.schema:
                        row[uk] = self._cast(uk, uv)
                count += 1
        return count

    def delete(self, filters: Dict[str, Any]) -> int:
        initial = len(self.rows)
        self.rows = [row for row in self.rows if not all(row.get(k) == v for k, v in filters.items())]
        return initial - len(self.rows)

    def _validate_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        for col, typ in self.schema.items():
            if col not in row_data:
                raise ValueError(f"Column {col} required")
            out[col] = self._cast(col, row_data[col])
        return out

    def _cast(self, col: str, value: Any) -> Any:
        typ = self.schema[col]
        if typ == "int":
            return int(value)
        elif typ == "str":
            return str(value)
        elif typ == "date":
            if isinstance(value, datetime.date):
                return value
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        else:
            raise ValueError(f"Type {typ} not supported for column {col}")


class AetherDB:
    """
    Main database engine. Manages tables and provides CRUD API.
    """
    def __init__(self):
        self.tables: Dict[str, Table] = {}
        from .auth import AuthManager
        from .utils import audit_log
        self.auth = AuthManager()
        self.current_user = None
        self.audit_log = audit_log
        # Bootstrap: create default 'aether' user if no users
        if not self.auth.users:
            self.auth.add_user("aether", "", role="admin", password_optional=True)
            self.current_user = "aether"
            self.audit_log("aether", "auto-login", "User created and auto-logged in")
            self.bootstrapped_user = True
        else:
            self.bootstrapped_user = False

    def add_user(self, username: str, password: str, role: str = "user"):
        self.auth.add_user(username, password, role)
        if self.current_user is None:
            self.current_user = username
            self.audit_log(username, "auto-login", "User created and auto-logged in")
        else:
            self.audit_log(self.current_user, "add_user", f"Added user {username} (role={role})")

    def login(self, username: str, password: str) -> bool:
        res = self.auth.authenticate(username, password)
        if res:
            self.audit_log(username, "login", "Login successful")
            self.current_user = username
        else:
            self.audit_log(username, "login_fail", f"Login failed")
        return res

    def require_login(self):
        if not self.current_user:
            raise PermissionError("Must login first.")

    def require_priv(self, priv: str):
        u = self.auth.get_user(self.current_user)
        if not u:
            raise PermissionError("Not logged in.")
        if priv == 'admin' and u.role != 'admin':
            raise PermissionError("Must be admin.")
        if priv == 'write' and u.role == 'readonly':
            raise PermissionError("Read-only user: modification not allowed.")

    def set_user_role(self, target_user: str, role: str):
        self.require_login()
        self.require_priv('admin')
        self.auth.set_role(self.current_user, target_user, role)
        self.audit_log(self.current_user, "set_role", f"{target_user} now {role}")

    def change_password(self, new_password: str):
        user = self.current_user
        if not user:
            raise PermissionError("No active user.")
        self.auth.change_password(user, new_password)
        self.audit_log(user, "passwd", "Changed user password.")

    # PATCH CRUD to require login and check role
    def create_table(self, table_name: str, schema: Dict[str, str]) -> None:
        self.require_login()
        u = self.auth.get_user(self.current_user)
        if u.role == 'readonly':
            raise PermissionError("Read-only user: cannot create tables.")
        if table_name in self.tables:
            raise ValueError(f"Table {table_name} already exists.")
        t = Table(table_name, schema, creator=self.current_user)
        self.tables[table_name] = t
        self.audit_log(self.current_user, "create_table", f"{table_name}")

    def check_perm(self, table_name, perm):
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist.")
        t = self.tables[table_name]
        if not t.has_perm(self.current_user, perm):
            raise PermissionError(f"No {perm} permission on {table_name} for {self.current_user}.")

    def insert(self, table_name: str, row_data: Dict[str, Any]) -> None:
        self.require_login()
        self.check_perm(table_name, 'write')
        self.audit_log(self.current_user, "insert", f"into {table_name}: {row_data}")
        return type(self).insert.__func__(self, table_name, row_data)

    def select(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        self.require_login()
        self.check_perm(table_name, 'read')
        self.audit_log(self.current_user, "select", f"from {table_name} ({filters})")
        return type(self).select.__func__(self, table_name, filters)

    def update(self, table_name: str, filters: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        self.require_login()
        self.check_perm(table_name, 'write')
        self.audit_log(self.current_user, "update", f"table {table_name}, set={update_data}, where={filters}")
        return type(self).update.__func__(self, table_name, filters, update_data)

    def delete(self, table_name: str, filters: Dict[str, Any]) -> int:
        self.require_login()
        self.check_perm(table_name, 'write')
        self.audit_log(self.current_user, "delete", f"from {table_name} where {filters}")
        return type(self).delete.__func__(self, table_name, filters)

    def grant(self, table: str, user: str, perm: str):
        self.require_login()
        self.check_perm(table, 'admin')
        self.tables[table].grant(user, perm)
        self.audit_log(self.current_user, "grant", f"{perm} on {table} to {user}")

    def revoke(self, table: str, user: str, perm: str):
        self.require_login()
        self.check_perm(table, 'admin')
        self.tables[table].revoke(user, perm)
        self.audit_log(self.current_user, "revoke", f"{perm} on {table} from {user}")

    def alter_table_rename(self, table, newname):
        self.require_login()
        self.require_priv('write')
        self.check_perm(table, 'admin')
        if newname in self.tables:
            raise ValueError(f"Table {newname} already exists.")
        self.tables[newname] = self.tables.pop(table)
        self.tables[newname].name = newname
        self.audit_log(self.current_user, "rename_table", f"{table} -> {newname}")
        return f"Table {table} renamed to {newname}."

    def alter_table_add_column(self, table, col, typ):
        self.require_login()
        self.require_priv('write')
        self.check_perm(table, 'admin')
        t = self.tables[table]
        if col in t.schema:
            raise ValueError(f"Column {col} already exists.")
        t.schema[col] = typ
        # Backfill default value (None)
        for row in t.rows:
            row[col] = None
        self.audit_log(self.current_user, "add_column", f"to {table}: {col} {typ}")
        return f"Column {col} added to table {table}."

    def execute_sql(self, sql: str):
        """Accept an SQL string, parse it, and dispatch to engine handlers."""
        from .query_parser import parse_sql, sql_to_engine_args
        parsed = parse_sql(sql)
        action, args = sql_to_engine_args(parsed)
        if action == 'create_table':
            return self.create_table(args['table'], args['schema'])
        elif action == 'insert':
            return self.insert(args['table'], args['row'])
        elif action == 'select':
            # select fields, but for MVP just returns all columns
            return self.select(args['table'], args.get('where'))
        elif action == 'update':
            return self.update(args['table'], args['where'], args['update'])
        elif action == 'delete':
            return self.delete(args['table'], args['where'])
        elif action == 'alter_rename':
            return self.alter_table_rename(args['table'], args['newname'])
        elif action == 'alter_addcol':
            return self.alter_table_add_column(args['table'], args['col'], args['type'])
        else:
            raise ValueError(f"Unknown SQL action {action}")

    def save_encrypted(self, file_path: str, password: str):
        """Serialize and encrypt the DB to a file."""
        import pickle
        from .encryption import encrypt
        data = pickle.dumps(self.tables)
        enc = encrypt(data, password)
        with open(file_path, "wb") as f:
            f.write(enc)

    @classmethod
    def load_encrypted(cls, file_path: str, password: str):
        """Load and decrypt DB from a file."""
        import pickle
        from .encryption import decrypt
        with open(file_path, "rb") as f:
            enc = f.read()
        data = decrypt(enc, password)
        obj = cls()
        obj.tables = pickle.loads(data)
        return obj
