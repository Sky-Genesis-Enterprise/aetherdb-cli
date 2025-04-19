"""
A minimal SQL parser for AetherDB supporting a subset of SQL CRUD queries.
"""
from typing import Any, Dict, List, Tuple
from pyparsing import (Word, alphas, alphanums, delimitedList, Group, Keyword,
                       Suppress, Literal, Optional, Forward, OneOrMore, QuotedString, nums, ParseException)
import re

# Supported keywords
CREATE, TABLE, INSERT, INTO, VALUES, SELECT, FROM, WHERE, UPDATE, SET, DELETE, ALTER, RENAME, TO, ADD, COLUMN = map(
    Keyword, "CREATE TABLE INSERT INTO VALUES SELECT FROM WHERE UPDATE SET DELETE ALTER RENAME TO ADD COLUMN".split())
INT, STR, DATE = map(Keyword, "INT STR DATE".split())

ident = Word(alphas, alphanums + "_" )
columnName = ident
columnType = INT | STR | DATE

integer = Word(nums)
string_literal = QuotedString('"') | QuotedString("'")
date_literal = QuotedString('"') | QuotedString("'")  # expects YYYY-MM-DD in quotes
value = integer | string_literal | date_literal

# CREATE TABLE mytable (id INT, name STR, birth DATE)
create_stmt = (CREATE + TABLE + ident('table') +
               Suppress('(') +
               Group(delimitedList(Group(columnName('col') + columnType('type'))))('columns') +
               Suppress(')'))

# INSERT INTO mytable (id, name) VALUES (1, "Alice")
insert_stmt = (INSERT + INTO + ident('table') +
               Suppress('(') + Group(delimitedList(columnName))('columns') + Suppress(')') +
               VALUES + Suppress('(') + Group(delimitedList(value))('values') + Suppress(')'))

# SELECT id, name FROM mytable WHERE name = 'Alice'
select_stmt = (SELECT + Group(delimitedList(columnName))('columns') +
               FROM + ident('table') +
               Optional(WHERE + Group(delimitedList(Group(columnName + Literal('=').suppress() + value)))('where')))

# UPDATE mytable SET name = 'Bob' WHERE id = 2
update_stmt = (UPDATE + ident('table') + SET +
               Group(delimitedList(Group(columnName + Literal('=').suppress() + value)))('set') +
               Optional(WHERE + Group(delimitedList(Group(columnName + Literal('=').suppress() + value)))('where')))

# DELETE FROM mytable WHERE name = 'Bob'
delete_stmt = (DELETE + FROM + ident('table') +
               Optional(WHERE + Group(delimitedList(Group(columnName + Literal('=').suppress() + value)))('where')))

# ALTER TABLE t RENAME TO newname
alter_rename_stmt = (ALTER + TABLE + ident('table') +
    RENAME + TO + ident('newname'))

# ALTER TABLE t ADD COLUMN col type
alter_addcol_stmt = (ALTER + TABLE + ident('table') +
    ADD + COLUMN + columnName('col') + columnType('type'))

sql_parser = create_stmt | insert_stmt | select_stmt | update_stmt | delete_stmt | alter_rename_stmt | alter_addcol_stmt

def parse_sql(sql: str) -> Any:
    """Parses a minimal SQL string and returns a parsed structure."""
    try:
        return sql_parser.parseString(sql, parseAll=True)
    except ParseException as pe:
        raise ValueError(f"SQL Parse error: {pe}")

# Helper to convert parsed results to Python data structures for the engine.
def sql_to_engine_args(parsed) -> Tuple[str, dict]:
    """Convert parsed SQL result to (action, data) for engine call."""
    action = None
    data = {}
    if 'CREATE' in parsed:
        action = 'create_table'
        cols = {col[0]: col[1].lower() for col in parsed.columns}
        data = {'table': parsed.table, 'schema': cols}
    elif 'INSERT' in parsed:
        action = 'insert'
        values = []
        for v in parsed.values:
            if re.match(r"^-?\d+$", v):
                values.append(int(v))
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", v.strip("'\"")):
                values.append(v.strip('"\''))
            else:
                values.append(v.strip('"\''))
        data = {
            'table': parsed.table,
            'row': dict(zip(parsed.columns, values))
        }
    elif 'SELECT' in parsed:
        action = 'select'
        where = None
        if parsed.get('where'):
            where = {k: v.strip('"\'') for k, v in parsed.where}
        data = {
            'table': parsed.table,
            'columns': list(parsed.columns),
            'where': where
        }
    elif 'UPDATE' in parsed:
        action = 'update'
        update_data = {k: v.strip('"\'') for k, v in parsed.set}
        where = None
        if parsed.get('where'):
            where = {k: v.strip('"\'') for k, v in parsed.where}
        data = {'table': parsed.table, 'update': update_data, 'where': where}
    elif 'DELETE' in parsed:
        action = 'delete'
        where = None
        if parsed.get('where'):
            where = {k: v.strip('"\'') for k, v in parsed.where}
        data = {'table': parsed.table, 'where': where}
    elif 'ALTER' in parsed:
        if 'RENAME' in parsed:
            action = 'alter_rename'
            data = {'table': parsed.table, 'newname': parsed.newname}
        elif 'ADD' in parsed and 'COLUMN' in parsed:
            action = 'alter_addcol'
            data = {'table': parsed.table, 'col': parsed.col, 'type': parsed.type.lower()}
        else:
            raise ValueError('ALTER TABLE: unrecognized format')
    else:
        raise ValueError(f"Unknown SQL operation: {parsed}")
    return action, data
