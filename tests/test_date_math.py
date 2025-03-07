import unittest

from pypika_tortoise import Field as F
from pypika_tortoise import Interval
from pypika_tortoise.context import DEFAULT_SQL_CONTEXT
from pypika_tortoise.dialects.mysql import MySQLQuery
from pypika_tortoise.dialects.oracle import OracleQuery
from pypika_tortoise.dialects.postgresql import PostgreSQLQuery

dt = F("dt")


class AddIntervalTests(unittest.TestCase):
    def test_add_microsecond(self):
        c = dt + Interval(microseconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1 MICROSECOND'", str(c))

    def test_add_second(self):
        c = dt + Interval(seconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1 SECOND'", str(c))

    def test_add_minute(self):
        c = dt + Interval(minutes=1)

        self.assertEqual("\"dt\"+INTERVAL '1 MINUTE'", str(c))

    def test_add_day(self):
        c = dt + Interval(days=1)

        self.assertEqual("\"dt\"+INTERVAL '1 DAY'", str(c))

    def test_add_week(self):
        c = dt + Interval(weeks=1)

        self.assertEqual("\"dt\"+INTERVAL '1 WEEK'", str(c))

    def test_add_month(self):
        c = dt + Interval(months=1)

        self.assertEqual("\"dt\"+INTERVAL '1 MONTH'", str(c))

    def test_add_quarter(self):
        c = dt + Interval(quarters=1)

        self.assertEqual("\"dt\"+INTERVAL '1 QUARTER'", str(c))

    def test_add_year(self):
        c = dt + Interval(years=1)

        self.assertEqual("\"dt\"+INTERVAL '1 YEAR'", str(c))

    def test_add_default(self):
        c = dt + Interval(days=0)

        self.assertEqual("\"dt\"+INTERVAL '0 DAY'", str(c))


class AddIntervalMultipleUnitsTests(unittest.TestCase):
    def test_add_second_microsecond(self):
        c = dt + Interval(seconds=1, microseconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1.1 SECOND_MICROSECOND'", str(c))

    def test_add_minute_microsecond(self):
        c = dt + Interval(minutes=1, microseconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1:0.1 MINUTE_MICROSECOND'", str(c))

    def test_add_minute_second(self):
        c = dt + Interval(minutes=1, seconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1:1 MINUTE_SECOND'", str(c))

    def test_add_hour_microsecond(self):
        c = dt + Interval(hours=1, microseconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1:0:0.1 HOUR_MICROSECOND'", str(c))

    def test_add_hour_second(self):
        c = dt + Interval(hours=1, seconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1:0:1 HOUR_SECOND'", str(c))

    def test_add_hour_minute(self):
        c = dt + Interval(hours=1, minutes=1)

        self.assertEqual("\"dt\"+INTERVAL '1:1 HOUR_MINUTE'", str(c))

    def test_add_day_microsecond(self):
        c = dt + Interval(days=1, microseconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1 0:0:0.1 DAY_MICROSECOND'", str(c))

    def test_add_day_second(self):
        c = dt + Interval(days=1, seconds=1)

        self.assertEqual("\"dt\"+INTERVAL '1 0:0:1 DAY_SECOND'", str(c))

    def test_add_day_minute(self):
        c = dt + Interval(days=1, minutes=1)

        self.assertEqual("\"dt\"+INTERVAL '1 0:1 DAY_MINUTE'", str(c))

    def test_add_day_hour(self):
        c = dt + Interval(days=1, hours=1)

        self.assertEqual("\"dt\"+INTERVAL '1 1 DAY_HOUR'", str(c))

    def test_add_year_month(self):
        c = dt + Interval(years=1, months=1)

        self.assertEqual("\"dt\"+INTERVAL '1-1 YEAR_MONTH'", str(c))

    def test_add_value_right(self):
        c = Interval(microseconds=1) - dt

        self.assertEqual("INTERVAL '1 MICROSECOND'-\"dt\"", str(c))

    def test_add_value_complex_expressions(self):
        c = dt + Interval(quarters=1) + Interval(weeks=1)

        self.assertEqual("\"dt\"+INTERVAL '1 QUARTER'+INTERVAL '1 WEEK'", str(c))


class DialectIntervalTests(unittest.TestCase):
    def test_mysql_dialect_uses_single_quotes_around_expression_in_an_interval(self):
        c = Interval(days=1).get_sql(MySQLQuery.SQL_CONTEXT)
        self.assertEqual("INTERVAL '1' DAY", c)

    def test_oracle_dialect_uses_single_quotes_around_expression_in_an_interval(self):
        c = Interval(days=1).get_sql(OracleQuery.SQL_CONTEXT)
        self.assertEqual("INTERVAL '1' DAY", c)

    def test_postgresql_dialect_uses_single_quotes_around_interval(self):
        c = Interval(days=1).get_sql(PostgreSQLQuery.SQL_CONTEXT)
        self.assertEqual("INTERVAL '1 DAY'", c)


class TestNegativeIntervals(unittest.TestCase):
    def test_day(self):
        c = Interval(days=-1).get_sql(DEFAULT_SQL_CONTEXT)
        self.assertEqual("INTERVAL '-1 DAY'", c)

    def test_week(self):
        c = Interval(weeks=-1).get_sql(DEFAULT_SQL_CONTEXT)
        self.assertEqual("INTERVAL '-1 WEEK'", c)

    def test_month(self):
        c = Interval(months=-1).get_sql(DEFAULT_SQL_CONTEXT)
        self.assertEqual("INTERVAL '-1 MONTH'", c)

    def test_year(self):
        c = Interval(years=-1).get_sql(DEFAULT_SQL_CONTEXT)
        self.assertEqual("INTERVAL '-1 YEAR'", c)

    def test_year_month(self):
        c = Interval(years=-1, months=-4).get_sql(DEFAULT_SQL_CONTEXT)
        self.assertEqual("INTERVAL '-1-4 YEAR_MONTH'", c)


class TruncateTrailingZerosTests(unittest.TestCase):
    def test_do_not_truncate_integer_values(self):
        i = Interval(seconds=10)

        self.assertEqual("INTERVAL '10 SECOND'", str(i))

    def test_do_not_truncate_months_between_years_and_datys(self):
        i = Interval(years=10, days=10)

        self.assertEqual("INTERVAL '10-0-10 YEAR_DAY'", str(i))
