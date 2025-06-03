import unittest

from pypika_tortoise import Field, JSONAttributeCriterion, Table
from pypika_tortoise.context import DEFAULT_SQL_CONTEXT
from pypika_tortoise.enums import Dialects


class JSONAttributeCriterionGeneralTests(unittest.TestCase):
    """General test cases for JSONAttributeCriterion class - initialization, aliases, table replacement, etc."""

    def setUp(self):
        self.table = Table("users")
        self.data_field = Field("data", table=self.table)

    def test_init_with_field_and_path(self):
        """Test initialization with a field and path."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "name"])

        self.assertEqual(criterion.json_column, self.data_field)
        self.assertEqual(criterion.path, ["user", "name"])
        self.assertIsNone(criterion.alias)

    def test_alias_with_with_alias_context(self):
        """Test that alias is included when with_alias is True."""
        criterion = JSONAttributeCriterion(self.data_field, ["name"], alias="user_name")
        ctx = DEFAULT_SQL_CONTEXT.copy(
            dialect=Dialects.POSTGRESQL, with_alias=True, with_namespace=True
        )

        expected = '"users"."data"->>\'name\' "user_name"'
        self.assertEqual(criterion.get_sql(ctx), expected)

    def test_replace_table(self):
        """Test replace_table functionality."""
        old_table = Table("old_users")
        new_table = Table("new_users")
        old_field = Field("data", table=old_table)

        criterion = JSONAttributeCriterion(old_field, ["user", "name"])
        updated_criterion = criterion.replace_table(old_table, new_table)

        # The @builder decorator creates a new instance, so they should be different objects
        # but the updated_criterion should have the new table
        ctx = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.POSTGRESQL, with_namespace=True)
        expected = "\"new_users\".\"data\"->'user'->>'name'"
        self.assertEqual(updated_criterion.get_sql(ctx), expected)

    def test_field_without_table(self):
        """Test with a field that has no table."""
        field = Field("data")
        criterion = JSONAttributeCriterion(field, ["user", "name"])

        ctx = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.POSTGRESQL)
        expected = '"data"->' + "'user'" + "->>" + "'name'"
        self.assertEqual(criterion.get_sql(ctx), expected)

    def test_unsupported_dialect_fallback(self):
        """Test that unsupported dialects fall back to PostgreSQL syntax."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "name"])
        ctx = DEFAULT_SQL_CONTEXT.copy(
            dialect=Dialects.ORACLE, with_namespace=True
        )  # Unsupported dialect

        # Should fall back to PostgreSQL syntax
        expected = '"users"."data"->' + "'user'" + "->>" + "'name'"
        self.assertEqual(criterion.get_sql(ctx), expected)


class JSONAttributeCriterionPostgreSQLTests(unittest.TestCase):
    """Test cases for JSONAttributeCriterion class with PostgreSQL dialect."""

    def setUp(self):
        self.table = Table("users")
        self.data_field = Field("data", table=self.table)
        self.ctx = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.POSTGRESQL, with_namespace=True)

    def test_postgres_sql_object_keys(self):
        """Test PostgreSQL SQL generation for nested object keys."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "details", "age"])

        expected = '"users"."data"->' + "'user'" + "->" + "'details'" + "->>" + "'age'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_sql_array_index(self):
        """Test PostgreSQL SQL generation for array index access."""
        criterion = JSONAttributeCriterion(self.data_field, ["tags", 0])

        expected = '"users"."data"->' + "'tags'" + "->>" + "0"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_sql_mixed_path(self):
        """Test PostgreSQL SQL generation for mixed object keys and array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "addresses", 0, "city"])

        expected = '"users"."data"->' + "'user'" + "->" + "'addresses'" + "->0->>" + "'city'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_sql_single_key(self):
        """Test PostgreSQL SQL generation for single key access."""
        criterion = JSONAttributeCriterion(self.data_field, ["name"])

        expected = '"users"."data"->>' + "'name'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_sql_single_index(self):
        """Test PostgreSQL SQL generation for single array index."""
        criterion = JSONAttributeCriterion(self.data_field, [0])

        expected = '"users"."data"->>0'
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_empty_path(self):
        """Test PostgreSQL behavior with empty path."""
        criterion = JSONAttributeCriterion(self.data_field, [])

        # PostgreSQL: should just return the column name
        expected = '"users"."data"'
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_numeric_keys_as_strings(self):
        """Test PostgreSQL handling of numeric keys (as strings) treated as object keys."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "123", "value"])

        expected = '"users"."data"->' + "'user'" + "->" + "'123'" + "->>" + "'value'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_negative_array_indices(self):
        """Test PostgreSQL behavior with negative array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["items", -1])

        # PostgreSQL: negative indices should use ->> for the last element
        expected = '"users"."data"->' + "'items'" + "->>" + "-1"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_postgres_complex_nested_path(self):
        """Test PostgreSQL with a complex nested path involving multiple arrays and objects."""
        path = ["users", 0, "profile", "addresses", 1, "location", "coordinates", 0]
        criterion = JSONAttributeCriterion(self.data_field, path)

        expected = (
            '"users"."data"->'
            + "'users'"
            + "->0->"
            + "'profile'"
            + "->"
            + "'addresses'"
            + "->1->"
            + "'location'"
            + "->"
            + "'coordinates'"
            + "->>"
            + "0"
        )
        self.assertEqual(criterion.get_sql(self.ctx), expected)


class JSONAttributeCriterionMySQLTests(unittest.TestCase):
    """Test cases for JSONAttributeCriterion class with MySQL dialect."""

    def setUp(self):
        self.table = Table("users")
        self.data_field = Field("data", table=self.table)
        self.ctx = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.MYSQL, with_namespace=True)

    def test_mysql_sql_object_keys(self):
        """Test MySQL SQL generation for nested object keys."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "details", "age"])

        expected = '"users"."data"->>\'' + "$.user.details.age" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_sql_array_index(self):
        """Test MySQL SQL generation for array index access."""
        criterion = JSONAttributeCriterion(self.data_field, ["tags", 0])

        expected = '"users"."data"->>\'' + "$.tags[0]" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_sql_mixed_path(self):
        """Test MySQL SQL generation for mixed object keys and array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "addresses", 0, "city"])

        expected = '"users"."data"->>\'' + "$.user.addresses[0].city" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_sql_single_key(self):
        """Test MySQL SQL generation for single key access."""
        criterion = JSONAttributeCriterion(self.data_field, ["name"])

        expected = '"users"."data"->>\'' + "$.name" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_sql_single_index(self):
        """Test MySQL SQL generation for single array index."""
        criterion = JSONAttributeCriterion(self.data_field, [0])

        expected = '"users"."data"->>\'' + "$[0]" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_empty_path(self):
        """Test MySQL behavior with empty path."""
        criterion = JSONAttributeCriterion(self.data_field, [])

        # MySQL: should return column with empty path
        expected = '"users"."data"->>\'' + "$" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_numeric_keys_as_strings(self):
        """Test MySQL handling of numeric keys (as strings) treated as object keys."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "123", "value"])

        expected = '"users"."data"->>\'' + "$.user.123.value" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_negative_array_indices(self):
        """Test MySQL behavior with negative array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["items", -1])

        expected = '"users"."data"->>\'' + "$.items[-1]" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mysql_complex_nested_path(self):
        """Test MySQL with a complex nested path involving multiple arrays and objects."""
        path = ["users", 0, "profile", "addresses", 1, "location", "coordinates", 0]
        criterion = JSONAttributeCriterion(self.data_field, path)

        expected = (
            '"users"."data"->>\'' + "$.users[0].profile.addresses[1].location.coordinates[0]" + "'"
        )
        self.assertEqual(criterion.get_sql(self.ctx), expected)


class JSONAttributeCriterionSQLiteTests(unittest.TestCase):
    """Test cases for JSONAttributeCriterion class with SQLite dialect."""

    def setUp(self):
        self.table = Table("users")
        self.data_field = Field("data", table=self.table)
        self.ctx = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.SQLITE, with_namespace=True)

    def test_sqlite_array_index(self):
        """Test SQLite SQL generation for array index access."""
        criterion = JSONAttributeCriterion(self.data_field, ["tags", 0])

        expected = '"users"."data"->>\'' + "$.tags[0]" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_sqlite_mixed_path(self):
        """Test SQLite SQL generation for mixed object keys and array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "addresses", 0, "city"])

        expected = '"users"."data"->>\'' + "$.user.addresses[0].city" + "'"
        self.assertEqual(criterion.get_sql(self.ctx), expected)


class JSONAttributeCriterionMSSQLTests(unittest.TestCase):
    """Test cases for JSONAttributeCriterion class with MS SQL Server dialect."""

    def setUp(self):
        self.table = Table("users")
        self.data_field = Field("data", table=self.table)
        self.ctx = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.MSSQL, with_namespace=True)

    def test_mssql_sql_object_keys(self):
        """Test MS SQL Server SQL generation for nested object keys."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "details", "age"])

        expected = 'JSON_VALUE("users"."data", ' + "'$.user.details.age'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_sql_array_index(self):
        """Test MS SQL Server SQL generation for array index access."""
        criterion = JSONAttributeCriterion(self.data_field, ["tags", 0])

        expected = 'JSON_VALUE("users"."data", ' + "'$.tags[0]'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_sql_mixed_path(self):
        """Test MS SQL Server SQL generation for mixed object keys and array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "addresses", 0, "city"])

        expected = 'JSON_VALUE("users"."data", ' + "'$.user.addresses[0].city'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_sql_single_key(self):
        """Test MS SQL Server SQL generation for single key access."""
        criterion = JSONAttributeCriterion(self.data_field, ["name"])

        expected = 'JSON_VALUE("users"."data", ' + "'$.name'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_sql_single_index(self):
        """Test MS SQL Server SQL generation for single array index."""
        criterion = JSONAttributeCriterion(self.data_field, [0])

        expected = 'JSON_VALUE("users"."data", ' + "'$[0]'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_empty_path(self):
        """Test MS SQL behavior with empty path."""
        criterion = JSONAttributeCriterion(self.data_field, [])

        # MS SQL: should return column with empty path
        expected = 'JSON_VALUE("users"."data", ' + "'$'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_numeric_keys_as_strings(self):
        """Test MS SQL handling of numeric keys (as strings) treated as object keys."""
        criterion = JSONAttributeCriterion(self.data_field, ["user", "123", "value"])

        expected = 'JSON_VALUE("users"."data", ' + "'$.user.123.value'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_negative_array_indices(self):
        """Test MS SQL behavior with negative array indices."""
        criterion = JSONAttributeCriterion(self.data_field, ["items", -1])

        expected = 'JSON_VALUE("users"."data", ' + "'$.items[-1]'" + ")"
        self.assertEqual(criterion.get_sql(self.ctx), expected)

    def test_mssql_complex_nested_path(self):
        """Test MS SQL with a complex nested path involving multiple arrays and objects."""
        path = ["users", 0, "profile", "addresses", 1, "location", "coordinates", 0]
        criterion = JSONAttributeCriterion(self.data_field, path)

        expected = (
            'JSON_VALUE("users"."data", '
            + "'$.users[0].profile.addresses[1].location.coordinates[0]'"
            + ")"
        )
        self.assertEqual(criterion.get_sql(self.ctx), expected)
