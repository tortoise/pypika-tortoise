import unittest

from pypika_tortoise import Table
from pypika_tortoise.dialects import SQLLiteQuery
from pypika_tortoise.exceptions import QueryException
from pypika_tortoise.functions import Avg
from pypika_tortoise.terms import Field


class SelectTests(unittest.TestCase):
    table_abc = Table("abc")

    def test_bool_true_as_one(self):
        q = SQLLiteQuery.from_("abc").select(True)

        self.assertEqual('SELECT 1 FROM "abc"', str(q))

    def test_bool_false_as_zero(self):
        q = SQLLiteQuery.from_("abc").select(False)

        self.assertEqual('SELECT 0 FROM "abc"', str(q))


class InsertTests(unittest.TestCase):
    table_abc = Table("abc")

    def test_insert_ignore(self):
        q = SQLLiteQuery.into("abc").insert((1, "a", True)).on_conflict().do_nothing()
        self.assertEqual("INSERT INTO \"abc\" VALUES (1,'a',true) ON CONFLICT DO NOTHING", str(q))

    def test_upsert(self):
        q = (
            SQLLiteQuery.into("abc")
            .insert(1, "b", False)
            .as_("aaa")
            .on_conflict(self.table_abc.id)
            .do_update("abc")
        )
        self.assertEqual(
            'INSERT INTO "abc" VALUES (1,\'b\',false) ON CONFLICT ("id") DO UPDATE SET "abc"=EXCLUDED."abc"',
            str(q),
        )

    def test_insert_default_values(self):
        q = SQLLiteQuery.into("abc").default_values()
        self.assertEqual('INSERT INTO "abc" DEFAULT VALUES', str(q))


class ReturningClauseTests(unittest.TestCase):
    table_abc = Table("abc")

    def test_insert_returning_one_field(self):
        query = SQLLiteQuery.into(self.table_abc).insert(1).returning(self.table_abc.id)
        self.assertEqual('INSERT INTO "abc" VALUES (1) RETURNING "id"', str(query))

    def test_insert_default_values_returning_one_field(self):
        query = SQLLiteQuery.into(self.table_abc).default_values().returning(self.table_abc.id)
        self.assertEqual('INSERT INTO "abc" DEFAULT VALUES RETURNING "id"', str(query))

    def test_update_returning(self):
        query = (
            SQLLiteQuery.update(self.table_abc)
            .where(self.table_abc.foo == 0)
            .set("foo", "bar")
            .returning("id")
        )
        self.assertEqual(
            'UPDATE "abc" SET "foo"=\'bar\' WHERE "foo"=0 RETURNING "abc"."id"', str(query)
        )

    def test_delete_returning(self):
        query = (
            SQLLiteQuery.from_(self.table_abc)
            .where(self.table_abc.foo == self.table_abc.bar)
            .delete()
            .returning(self.table_abc.id)
        )
        self.assertEqual('DELETE FROM "abc" WHERE "foo"="bar" RETURNING "id"', str(query))

    def test_returning_from_missing_table_raises_queryexception(self):
        field_from_diff_table = Field("xyz", table=Table("other"))
        with self.assertRaisesRegex(QueryException, "You can't return from other tables"):
            (
                SQLLiteQuery.from_(self.table_abc)
                .where(self.table_abc.foo == self.table_abc.bar)
                .delete()
                .returning(field_from_diff_table)
            )

    def test_insert_returning_aggregate(self):
        with self.assertRaisesRegex(
            QueryException, "Aggregate functions are not allowed in returning"
        ):
            SQLLiteQuery.into(self.table_abc).insert(1).returning(Avg(self.table_abc.views))
