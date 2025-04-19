from aetherdb.db_engine import AetherDB

# Initialize database
adb = AetherDB()

# Create table example: users (id, name, birthdate)
adb.create_table("users", {
    "id": "int",
    "name": "str",
    "birthdate": "date",
})

# Insert users
adb.insert("users", {"id": 1, "name": "Alice", "birthdate": "1990-04-10"})
adb.insert("users", {"id": 2, "name": "Bob", "birthdate": "1985-12-23"})

# Select all users
users = adb.select("users")
print("All Users:", users)

# Select users by filter
alice = adb.select("users", {"name": "Alice"})
print("Alice record:", alice)

# Update a user
adb.update("users", {"id": 2}, {"name": "Robert"})
print("After update:", adb.select("users"))

# Delete a user
adb.delete("users", {"id": 1})
print("After delete:", adb.select("users"))

# Now the same operations via SQL queries:
adb.execute_sql('CREATE TABLE accounts (id INT, owner STR, opened DATE)')
adb.execute_sql('INSERT INTO accounts (id, owner, opened) VALUES (101, "Eve", "2022-01-01")')
adb.execute_sql('INSERT INTO accounts (id, owner, opened) VALUES (102, "Foo", "2022-02-02")')

print("SQL select:", adb.execute_sql('SELECT id, owner FROM accounts WHERE owner = "Eve"'))
adb.execute_sql('UPDATE accounts SET owner = "Mallory" WHERE id = 102')
print("After SQL UPDATE:", adb.execute_sql('SELECT id, owner, opened FROM accounts'))
adb.execute_sql('DELETE FROM accounts WHERE owner = "Eve"')
print("After SQL DELETE:", adb.execute_sql('SELECT id, owner, opened FROM accounts'))

# Demonstrate encrypted save/load:
passwd = "letmein123"  # In practice, use a secure password prompt!
adb.save_encrypted("example_db.aes", passwd)
print("DB saved as encrypted .aes file.")

adb2 = adb.load_encrypted("example_db.aes", passwd)
print("Loaded from encrypted.", adb2.select("users"))
