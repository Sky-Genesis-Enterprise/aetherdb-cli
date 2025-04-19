import unittest
from aetherdb.db_engine import AetherDB
from datetime import date

class TestAetherDBEngine(unittest.TestCase):
    def setUp(self):
        self.db = AetherDB()
        self.schema = {"id": "int", "name": "str", "birth": "date"}
        self.db.create_table("users", self.schema)

    def test_insert_and_select(self):
        self.db.insert("users", {"id": 1, "name": "Alice", "birth": "1990-02-02"})
        users = self.db.select("users")
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["name"], "Alice")
        self.assertEqual(users[0]["birth"], date(1990, 2, 2))

    def test_filter_select(self):
        self.db.insert("users", {"id": 2, "name": "Bob", "birth": "1991-03-03"})
        result = self.db.select("users", {"id": 2})
        self.assertEqual(result[0]["name"], "Bob")

    def test_update(self):
        self.db.insert("users", {"id": 3, "name": "Eve", "birth": "1992-04-04"})
        n = self.db.update("users", {"id": 3}, {"name": "Evelyn"})
        self.assertEqual(n, 1)
        self.assertEqual(self.db.select("users", {"id": 3})[0]["name"], "Evelyn")

    def test_delete(self):
        self.db.insert("users", {"id": 4, "name": "Carl", "birth": "1993-05-05"})
        n = self.db.delete("users", {"name": "Carl"})
        self.assertEqual(n, 1)
        self.assertEqual(len(self.db.select("users", {"name": "Carl"})), 0)

    def test_sql_crud(self):
        self.db.execute_sql('CREATE TABLE people (id INT, n STR, d DATE)')
        self.db.execute_sql('INSERT INTO people (id, n, d) VALUES (7, "Test", "2005-06-07")')
        out = self.db.execute_sql('SELECT id, n FROM people WHERE id = 7')
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["n"], "Test")
        self.db.execute_sql('UPDATE people SET n = "T2" WHERE id = 7')
        out2 = self.db.execute_sql('SELECT id, n FROM people WHERE n = "T2"')
        self.assertEqual(out2[0]["id"], 7)
        self.db.execute_sql('DELETE FROM people WHERE n = "T2"')
        self.assertEqual(len(self.db.execute_sql('SELECT id, n FROM people')), 0)

if __name__ == "__main__":
    unittest.main()
