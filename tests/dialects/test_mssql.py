import unittest

from pypika_tortoise import Field as F
from pypika_tortoise import Table
from pypika_tortoise.dialects import MSSQLQuery


class PowerTests(unittest.TestCase):
    t = Table("abc")

    def test_select_with_double_stars(self):
        q1 = MSSQLQuery.from_("abc").select(F("a") / (F("b") ** 2))
        q2 = MSSQLQuery.from_(self.t).select(self.t.a / (self.t.b**2))
        q3 = MSSQLQuery.from_("abc").select(F("a") ** (F("b") / 2))
        q4 = MSSQLQuery.from_(self.t).select(self.t.a ** (self.t.b / 2))
        q5 = MSSQLQuery.from_("abc").select((F("a") ** F("b")) ** 2)
        q6 = MSSQLQuery.from_(self.t).select((self.t.a**self.t.b) ** 2)

        self.assertEqual('SELECT "a"/POWER("b",2) FROM "abc"', str(q1))
        self.assertEqual('SELECT "a"/POWER("b",2) FROM "abc"', str(q2))
        self.assertEqual('SELECT POWER("a","b"/2) FROM "abc"', str(q3))
        self.assertEqual('SELECT POWER("a","b"/2) FROM "abc"', str(q4))
        self.assertEqual('SELECT POWER(POWER("a","b"),2) FROM "abc"', str(q5))
        self.assertEqual('SELECT POWER(POWER("a","b"),2) FROM "abc"', str(q6))
