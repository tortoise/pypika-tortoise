import unittest

from pypika_tortoise import Tables
from pypika_tortoise import functions as fn
from pypika_tortoise.context import DEFAULT_SQL_CONTEXT
from pypika_tortoise.terms import ValueWrapper


class NegationTests(unittest.TestCase):
    table_abc, table_efg = Tables("abc", "efg")

    def test_negate_wrapped_float(self):
        q = -ValueWrapper(1.0)

        self.assertEqual("-1.0", q.get_sql(DEFAULT_SQL_CONTEXT))

    def test_negate_wrapped_int(self):
        q = -ValueWrapper(1)

        self.assertEqual("-1", q.get_sql(DEFAULT_SQL_CONTEXT))

    def test_negate_field(self):
        q = -self.table_abc.foo

        self.assertEqual(
            '-"abc"."foo"', q.get_sql(DEFAULT_SQL_CONTEXT.copy(with_namespace=True, quote_char='"'))
        )

    def test_negate_function(self):
        q = -fn.Sum(self.table_abc.foo)

        self.assertEqual(
            '-SUM("abc"."foo")',
            q.get_sql(DEFAULT_SQL_CONTEXT.copy(with_namespace=True, quote_char='"')),
        )
