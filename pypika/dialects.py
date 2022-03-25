import itertools
from copy import copy
from datetime import time
from typing import Any, Union

from pypika.enums import Dialects
from pypika.queries import Query, QueryBuilder, Table
from pypika.terms import ArithmeticExpression, Field, Function, Star, Term, ValueWrapper
from pypika.utils import QueryException, builder, format_alias_sql, format_quotes


class MySQLQuery(Query):
    """
    Defines a query class for use with MySQL.
    """

    @classmethod
    def _builder(cls, **kwargs: Any) -> "MySQLQueryBuilder":
        return MySQLQueryBuilder(**kwargs)

    @classmethod
    def load(cls, fp: str) -> "MySQLLoadQueryBuilder":
        return MySQLLoadQueryBuilder().load(fp)


class MySQLValueWrapper(ValueWrapper):
    def get_value_sql(self, **kwargs: Any) -> str:
        quote_char = kwargs.get("secondary_quote_char") or ""
        if isinstance(self.value, str):
            value = self.value.replace(quote_char, quote_char * 2)
            value = value.replace("\\", "\\\\")
            return format_quotes(value, quote_char)
        elif isinstance(self.value, time):
            value = self.value.replace(tzinfo=None)
            return format_quotes(value.isoformat(), quote_char)
        return super(MySQLValueWrapper, self).get_value_sql(**kwargs)


class MySQLQueryBuilder(QueryBuilder):
    QUOTE_CHAR = "`"
    QUERY_CLS = MySQLQuery

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            dialect=Dialects.MYSQL,
            wrapper_cls=MySQLValueWrapper,
            wrap_set_operation_queries=False,
            **kwargs,
        )
        self._modifiers = []

    def _on_conflict_sql(self, **kwargs: Any) -> str:
        kwargs["alias_quote_char"] = (
            self.ALIAS_QUOTE_CHAR
            if self.QUERY_ALIAS_QUOTE_CHAR is None
            else self.QUERY_ALIAS_QUOTE_CHAR
        )
        kwargs["as_keyword"] = True
        querystring = format_alias_sql("", self.alias, **kwargs)
        return querystring

    def get_sql(self, **kwargs: Any) -> str:
        self._set_kwargs_defaults(kwargs)
        querystring = super(MySQLQueryBuilder, self).get_sql(**kwargs)
        if querystring:
            if self._update_table:
                if self._orderbys:
                    querystring += self._orderby_sql(**kwargs)
                if self._limit:
                    querystring += self._limit_sql()
        return querystring

    def _on_conflict_action_sql(self, **kwargs: Any) -> str:
        kwargs.pop("with_namespace", None)
        if len(self._on_conflict_do_updates) > 0:
            updates = []
            for field, value in self._on_conflict_do_updates:
                if value:
                    updates.append(
                        "{field}={value}".format(
                            field=field.get_sql(**kwargs),
                            value=value.get_sql(**kwargs),
                        )
                    )
                else:
                    updates.append(
                        "{field}={alias_quote_char}{alias}{alias_quote_char}.{value}".format(
                            alias_quote_char=self.QUOTE_CHAR,
                            field=field.get_sql(**kwargs),
                            alias=self.alias,
                            value=field.get_sql(**kwargs),
                        )
                    )
            action_sql = " ON DUPLICATE KEY UPDATE {updates}".format(updates=",".join(updates))
            return action_sql
        return ""

    @builder
    def modifier(self, value: str) -> "MySQLQueryBuilder":
        """
        Adds a modifier such as SQL_CALC_FOUND_ROWS to the query.
        https://dev.mysql.com/doc/refman/5.7/en/select.html

        :param value: The modifier value e.g. SQL_CALC_FOUND_ROWS
        """
        self._modifiers.append(value)

    def _select_sql(self, **kwargs: Any) -> str:
        """
        Overridden function to generate the SELECT part of the SQL statement,
        with the addition of the a modifier if present.
        """
        return "SELECT {distinct}{modifier}{select}".format(
            distinct="DISTINCT " if self._distinct else "",
            modifier="{} ".format(" ".join(self._modifiers)) if self._modifiers else "",
            select=",".join(
                term.get_sql(with_alias=True, subquery=True, **kwargs) for term in self._selects
            ),
        )

    def _insert_sql(self, **kwargs: Any) -> str:
        return "INSERT {ignore}INTO {table}".format(
            table=self._insert_table.get_sql(**kwargs),
            ignore="IGNORE " if self._on_conflict_do_nothing else "",
        )


class MySQLLoadQueryBuilder:
    QUERY_CLS = MySQLQuery

    def __init__(self) -> None:
        self._load_file = None
        self._into_table = None

    @builder
    def load(self, fp: str) -> "MySQLLoadQueryBuilder":
        self._load_file = fp

    @builder
    def into(self, table: Union[str, Table]) -> "MySQLLoadQueryBuilder":
        self._into_table = table if isinstance(table, Table) else Table(table)

    def get_sql(self, *args: Any, **kwargs: Any) -> str:
        querystring = ""
        if self._load_file and self._into_table:
            querystring += self._load_file_sql(**kwargs)
            querystring += self._into_table_sql(**kwargs)
            querystring += self._options_sql(**kwargs)

        return querystring

    def _load_file_sql(self, **kwargs: Any) -> str:
        return "LOAD DATA LOCAL INFILE '{}'".format(self._load_file)

    def _into_table_sql(self, **kwargs: Any) -> str:
        return " INTO TABLE `{}`".format(self._into_table.get_sql(**kwargs))

    def _options_sql(self, **kwargs: Any) -> str:
        return " FIELDS TERMINATED BY ','"

    def __str__(self) -> str:
        return self.get_sql()


class PostgreSQLQuery(Query):
    """
    Defines a query class for use with PostgreSQL.
    """

    @classmethod
    def _builder(cls, **kwargs) -> "PostgreSQLQueryBuilder":
        return PostgreSQLQueryBuilder(**kwargs)


class PostgreSQLQueryBuilder(QueryBuilder):
    ALIAS_QUOTE_CHAR = '"'
    QUERY_CLS = PostgreSQLQuery

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(dialect=Dialects.POSTGRESQL, **kwargs)
        self._returns = []
        self._return_star = False

        self._distinct_on = []

    def __copy__(self) -> "PostgreSQLQueryBuilder":
        newone = super().__copy__()
        newone._returns = copy(self._returns)
        newone._on_conflict_do_updates = copy(self._on_conflict_do_updates)
        return newone

    @builder
    def distinct_on(self, *fields: Union[str, Term]) -> "PostgreSQLQueryBuilder":
        for field in fields:
            if isinstance(field, str):
                self._distinct_on.append(Field(field))
            elif isinstance(field, Term):
                self._distinct_on.append(field)

    def _distinct_sql(self, **kwargs: Any) -> str:
        if self._distinct_on:
            return "DISTINCT ON({distinct_on}) ".format(
                distinct_on=",".join(
                    term.get_sql(with_alias=True, **kwargs) for term in self._distinct_on
                )
            )
        return super()._distinct_sql(**kwargs)

    @builder
    def returning(self, *terms: Any) -> "PostgreSQLQueryBuilder":
        for term in terms:
            if isinstance(term, Field):
                self._return_field(term)
            elif isinstance(term, str):
                self._return_field_str(term)
            elif isinstance(term, ArithmeticExpression):
                self._return_other(term)
            elif isinstance(term, Function):
                raise QueryException("Aggregate functions are not allowed in returning")
            else:
                self._return_other(self.wrap_constant(term, self._wrapper_cls))

    def _validate_returning_term(self, term: Term) -> None:
        for field in term.fields_():
            if not any([self._insert_table, self._update_table, self._delete_from]):
                raise QueryException("Returning can't be used in this query")

            table_is_insert_or_update_table = field.table in {
                self._insert_table,
                self._update_table,
            }
            join_tables = set(
                itertools.chain.from_iterable([j.criterion.tables_ for j in self._joins])
            )
            join_and_base_tables = set(self._from) | join_tables
            table_not_base_or_join = bool(term.tables_ - join_and_base_tables)
            if not table_is_insert_or_update_table and table_not_base_or_join:
                raise QueryException("You can't return from other tables")

    def _set_returns_for_star(self) -> None:
        self._returns = [
            returning for returning in self._returns if not hasattr(returning, "table")
        ]
        self._return_star = True

    def _return_field(self, term: Union[str, Field]) -> None:
        if self._return_star:
            # Do not add select terms after a star is selected
            return

        self._validate_returning_term(term)

        if isinstance(term, Star):
            self._set_returns_for_star()

        self._returns.append(term)

    def _return_field_str(self, term: Union[str, Field]) -> None:
        if term == "*":
            self._set_returns_for_star()
            self._returns.append(Star())
            return

        if self._insert_table:
            self._return_field(Field(term, table=self._insert_table))
        elif self._update_table:
            self._return_field(Field(term, table=self._update_table))
        elif self._delete_from:
            self._return_field(Field(term, table=self._from[0]))
        else:
            raise QueryException("Returning can't be used in this query")

    def _return_other(self, function: Term) -> None:
        self._validate_returning_term(function)
        self._returns.append(function)

    def _returning_sql(self, **kwargs: Any) -> str:
        return " RETURNING {returning}".format(
            returning=",".join(term.get_sql(with_alias=True, **kwargs) for term in self._returns),
        )

    def get_sql(self, with_alias: bool = False, subquery: bool = False, **kwargs: Any) -> str:
        self._set_kwargs_defaults(kwargs)
        querystring = super(PostgreSQLQueryBuilder, self).get_sql(with_alias, subquery, **kwargs)
        if self._returns:
            kwargs["with_namespace"] = self._update_table and self.from_
            querystring += self._returning_sql(**kwargs)
        return querystring


class SQLLiteValueWrapper(ValueWrapper):
    def get_value_sql(self, **kwargs: Any) -> str:
        if isinstance(self.value, bool):
            return "1" if self.value else "0"
        return super().get_value_sql(**kwargs)


class SQLLiteQuery(Query):
    """
    Defines a query class for use with Microsoft SQL Server.
    """

    @classmethod
    def _builder(cls, **kwargs: Any) -> "SQLLiteQueryBuilder":
        return SQLLiteQueryBuilder(**kwargs)


class SQLLiteQueryBuilder(QueryBuilder):
    QUERY_CLS = SQLLiteQuery

    def __init__(self, **kwargs):
        super(SQLLiteQueryBuilder, self).__init__(
            dialect=Dialects.SQLITE, wrapper_cls=SQLLiteValueWrapper, **kwargs
        )

    def get_sql(self, **kwargs: Any) -> str:
        self._set_kwargs_defaults(kwargs)
        querystring = super(SQLLiteQueryBuilder, self).get_sql(**kwargs)
        if querystring:
            if self._update_table:
                if self._orderbys:
                    querystring += self._orderby_sql(**kwargs)
                if self._limit:
                    querystring += self._limit_sql()
        return querystring
