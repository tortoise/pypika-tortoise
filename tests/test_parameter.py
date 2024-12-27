import unittest
from datetime import date

from pypika_tortoise import Parameter, Query, Tables, ValueWrapper
from pypika_tortoise.dialects.mssql import MSSQLQuery
from pypika_tortoise.dialects.mysql import MySQLQuery
from pypika_tortoise.dialects.postgresql import PostgreSQLQuery
from pypika_tortoise.enums import Dialects
from pypika_tortoise.functions import Upper
from pypika_tortoise.terms import Case, Parameterizer


class ParametrizedTests(unittest.TestCase):
    table_abc, table_efg = Tables("abc", "efg")

    def test_param_insert(self):
        q = (
            Query.into(self.table_abc)
            .columns("a", "b", "c")
            .insert(Parameter("?"), Parameter("?"), Parameter("?"))
        )

        self.assertEqual('INSERT INTO "abc" ("a","b","c") VALUES (?,?,?)', q.get_sql())

    def test_param_select_join(self):
        q = (
            Query.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.category == Parameter("%s"))
            .join(self.table_efg)
            .on(self.table_abc.id == self.table_efg.abc_id)
            .where(self.table_efg.date >= Parameter("%s"))
            .limit(10)
        )

        self.assertEqual(
            'SELECT * FROM "abc" JOIN "efg" ON "abc"."id"="efg"."abc_id" '
            'WHERE "abc"."category"=%s AND "efg"."date">=%s LIMIT 10',
            q.get_sql(),
        )

    def test_param_select_subquery(self):
        q = (
            Query.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.category == Parameter("&1"))
            .where(
                self.table_abc.id.isin(
                    Query.from_(self.table_efg)
                    .select(self.table_efg.abc_id)
                    .where(self.table_efg.date >= Parameter("&2"))
                )
            )
            .limit(10)
        )

        self.assertEqual(
            'SELECT * FROM "abc" WHERE "category"=&1 AND "id" IN '
            '(SELECT "abc_id" FROM "efg" WHERE "date">=&2) LIMIT 10',
            q.get_sql(),
        )

    def test_join(self):
        subquery = (
            Query.from_(self.table_efg)
            .select(self.table_efg.fiz, self.table_efg.buz)
            .where(self.table_efg.buz == Parameter(":buz"))
        )

        q = (
            Query.from_(self.table_abc)
            .join(subquery)
            .on(self.table_abc.bar == subquery.buz)
            .select(self.table_abc.foo, subquery.fiz)
            .where(self.table_abc.bar == Parameter(":bar"))
        )

        self.assertEqual(
            'SELECT "abc"."foo","sq0"."fiz" FROM "abc" JOIN (SELECT "fiz","buz" FROM "efg" WHERE "buz"=:buz)'
            ' "sq0" ON "abc"."bar"="sq0"."buz" WHERE "abc"."bar"=:bar',
            q.get_sql(),
        )

    def test_qmark_parameter(self):
        self.assertEqual("?", Parameter("?").get_sql())

    def test_oracle(self):
        self.assertEqual("?", Parameter(idx=1).get_sql(dialect=Dialects.ORACLE))
        self.assertEqual("?", Parameter(idx=2).get_sql(dialect=Dialects.ORACLE))

    def test_mssql(self):
        self.assertEqual("?", Parameter(idx=1).get_sql(dialect=Dialects.MSSQL))
        self.assertEqual("?", Parameter(idx=2).get_sql(dialect=Dialects.MSSQL))

    def test_mysql(self):
        self.assertEqual("%s", Parameter(idx=1).get_sql(dialect=Dialects.MYSQL))
        self.assertEqual("%s", Parameter(idx=2).get_sql(dialect=Dialects.MYSQL))

    def test_postgres(self):
        self.assertEqual("$1", Parameter(idx=1).get_sql(dialect=Dialects.POSTGRESQL))
        self.assertEqual("$2", Parameter(idx=2).get_sql(dialect=Dialects.POSTGRESQL))

    def test_sqlite(self):
        self.assertEqual("?", Parameter(idx=1).get_sql(dialect=Dialects.SQLITE))
        self.assertEqual("?", Parameter(idx=2).get_sql(dialect=Dialects.SQLITE))


class ParameterizerTests(unittest.TestCase):
    table_abc, table_efg = Tables("abc", "efg")

    def test_param_insert(self):
        q = Query.into(self.table_abc).columns("a", "b", "c").insert(1, 2.2, "foo")

        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer)
        self.assertEqual('INSERT INTO "abc" ("a","b","c") VALUES (?,?,?)', sql)
        self.assertEqual([1, 2.2, "foo"], parameterizer.values)

    def test_select_join_in_mysql(self):
        q = (
            MySQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.category == "foobar")
            .join(self.table_efg)
            .on(self.table_abc.id == self.table_efg.abc_id)
            .where(self.table_efg.date >= date(2024, 2, 22))
            .limit(10)
        )

        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer, dialect=Dialects.MYSQL)
        self.assertEqual(
            "SELECT * FROM `abc` JOIN `efg` ON `abc`.`id`=`efg`.`abc_id` WHERE `abc`.`category`=%s AND `efg`.`date`>=%s LIMIT %s",
            sql,
        )
        self.assertEqual(["foobar", date(2024, 2, 22), 10], parameterizer.values)

    def test_select_subquery_in_postgres(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.category == "foobar")
            .where(
                self.table_abc.id.isin(
                    Query.from_(self.table_efg)
                    .select(self.table_efg.abc_id)
                    .where(self.table_efg.date >= date(2024, 2, 22))
                )
            )
            .limit(10)
        )

        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer, dialect=Dialects.POSTGRESQL)
        self.assertEqual(
            'SELECT * FROM "abc" WHERE "category"=$1 AND "id" IN (SELECT "abc_id" FROM "efg" WHERE "date">=$2) LIMIT $3',
            sql,
        )
        self.assertEqual(["foobar", date(2024, 2, 22), 10], parameterizer.values)

    def test_join_in_postgres(self):
        subquery = (
            Query.from_(self.table_efg)
            .select(self.table_efg.fiz, self.table_efg.buz)
            .where(self.table_efg.buz == "buz")
        )

        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .join(subquery)
            .on(self.table_abc.bar == subquery.buz)
            .select(self.table_abc.foo, subquery.fiz)
            .where(self.table_abc.bar == "bar")
        )

        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer, dialect=Dialects.POSTGRESQL)
        self.assertEqual(
            'SELECT "abc"."foo","sq0"."fiz" FROM "abc" JOIN (SELECT "fiz","buz" FROM "efg" WHERE "buz"=$1)'
            ' "sq0" ON "abc"."bar"="sq0"."buz" WHERE "abc"."bar"=$2',
            sql,
        )
        self.assertEqual(["buz", "bar"], parameterizer.values)

    def test_function_parameter(self):
        q = (
            Query.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.category == Upper(ValueWrapper("foobar")))
        )
        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer)
        self.assertEqual('SELECT * FROM "abc" WHERE "category"=UPPER(?)', sql)

        self.assertEqual(["foobar"], parameterizer.values)

    def test_case_when_in_select(self):
        q = Query.from_(self.table_abc).select(
            Case().when(self.table_abc.category == "foobar", 1).else_(2)
        )
        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer)
        self.assertEqual('SELECT CASE WHEN "category"=? THEN ? ELSE ? END FROM "abc"', sql)
        self.assertEqual(["foobar", 1, 2], parameterizer.values)

    def test_case_when_in_where(self):
        q = (
            Query.from_(self.table_abc)
            .select("*")
            .where(
                self.table_abc.category_int
                > Case().when(self.table_abc.category == "foobar", 1).else_(2)
            )
        )
        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer)
        self.assertEqual(
            'SELECT * FROM "abc" WHERE "category_int">CASE WHEN "category"=? THEN ? ELSE ? END',
            sql,
        )
        self.assertEqual(["foobar", 1, 2], parameterizer.values)

    def test_limit_and_offest(self):
        q = Query.from_(self.table_abc).select("*").limit(10).offset(5)
        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer)
        self.assertEqual('SELECT * FROM "abc" LIMIT ? OFFSET ?', sql)
        self.assertEqual([10, 5], parameterizer.values)

    def test_limit_and_offest_in_mssql(self):
        q = MSSQLQuery.from_(self.table_abc).select("*").limit(10).offset(5)
        parameterizer = Parameterizer()
        sql = q.get_sql(parameterizer=parameterizer)
        self.assertEqual(
            'SELECT * FROM "abc" ORDER BY (SELECT 0) OFFSET ? ROWS FETCH NEXT ? ROWS ONLY', sql
        )
        self.assertEqual([5, 10], parameterizer.values)

    def test_placeholder_factory(self):
        parameterizer = Parameterizer(placeholder_factory=lambda _: "%s")
        param = parameterizer.create_param(1)
        self.assertEqual("%s", param.get_sql())
