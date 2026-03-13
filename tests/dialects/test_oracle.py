import unittest

from pypika_tortoise.dialects import OracleQuery


class InsertTests(unittest.TestCase):
    def test_insert_default_values(self):
        q = OracleQuery.into("abc").default_values()
        self.assertEqual('INSERT INTO "abc" DEFAULT VALUES', str(q))
