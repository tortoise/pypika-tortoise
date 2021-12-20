import unittest

from pypika import Table
from pypika.dialects import SQLLiteQuery


class SelectTests(unittest.TestCase):
    table_abc = Table("abc")

    def test_bool_true_as_one(self):
        q = SQLLiteQuery.from_("abc").select(True)

        self.assertEqual('SELECT 1 FROM "abc"', str(q))

    def test_bool_false_as_zero(self):
        q = SQLLiteQuery.from_("abc").select(False)

        self.assertEqual('SELECT 0 FROM "abc"', str(q))


class InsertTests(unittest.TestCase):
    def test_insert_ignore(self):
        q = SQLLiteQuery.into("abc").insert((1, "a", True)).ignore()
        self.assertEqual("INSERT OR IGNORE INTO \"abc\" VALUES (1,'a',true)", str(q))
