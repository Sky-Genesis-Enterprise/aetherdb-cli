# AetherDB

AetherDB is a PostgreSQL-inspired custom database MVP, designed for easy deployment and secure operation on both Linux and Windows platforms.

## Features (MVP)
- Core CRUD operations (Create, Read, Update, Delete)
- Support for essential data types (integers, strings, dates, etc.)
- Basic SQL query support (data manipulation & retrieval)
- Basic SQL DDL: `ALTER TABLE ... RENAME TO ...`, `ALTER TABLE ... ADD COLUMN ...`
- AES-256 encryption for secure storage
- Basic access controls and user authentication
- Simple installation scripts for Linux (`install.sh`) and Windows (`install.bat`)
- Python virtual environment setup
- Unit tests and benchmarking suite
- Auditing: all changes and access logged to `aetherdb_audit.log`

## Installation

**Linux:**
```bash
chmod +x install.sh
bash install.sh
# You can now launch the CLI from anywhere using:
aetherdb
```

**Windows:**
```bat
install.bat
:: Add the project directory to your PATH, or copy 'aetherdb.bat' to a directory already in PATH
aetherdb
```

## Usage Example
See `examples/example_usage.py` for how to initialize the DB, create tables, and run SQL commands.

## Interactive Client (psql-inspired)
Run the interactive CLI:

```bash
source .venv/bin/activate   # Linux/macOS
# or
call .venv\Scripts\activate.bat  # Windows

python -m aetherdb.client
```

### CLI features
- Enter SQL commands (end with a semicolon)
- Meta-commands:
    - `\\dt` — List tables
    - `\\d [table]` — Show schema for a table, or all tables’ schemas if no argument, now also shows user-permission matrix for tables
    - `\\grant <perm> on <table> to <user>` — Grant table permission (read, write, admin)
    - `\\revoke <perm> on <table> from <user>` — Revoke table permission
    - `\\help` — Show help
    - `\\q` — Quit
    - `\\save <path>` — Save database to an AES-256 encrypted file
    - `\\load <path>` — Load encrypted database file
    - `\\adduser` — Create a new user and log in
    - `\\login [username]` — Log in as a user
    - `\\whoami` — Show the current user
    - `\\passwd` — Set/change the current user’s password (recommended immediately!)
    - `\\role <user> <role>` — Assign a role to a user (admin only)
    - `\\du` — View user list and current roles
    - `\\log [N|all]` — Show latest audit log entries (user, timestamp, action, details)
    - All table operations require login
    - Prompts securely for password

- System user roles: `admin`, `user`, `readonly`. Role affects global capabilities.
- On installation/first run: System auto-creates a default `aether` user (admin, no password).
- Login as `aether` is automatic on first session if no users exist; you will see a warning.

---

## Development & Testing
- Run tests: `python -m unittest discover tests`

## License
Apache License 2.0