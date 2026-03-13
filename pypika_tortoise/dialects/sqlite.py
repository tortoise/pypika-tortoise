from __future__ import annotations

import itertools
from copy import copy
from typing import Any

from ..context import DEFAULT_SQL_CONTEXT, SqlContext
from ..enums import Dialects
from ..exceptions import QueryException
from ..queries import Query, QueryBuilder
from ..terms import ArithmeticExpression, Field, Function, Star, Term, ValueWrapper
from ..utils import builder


class SQLLiteValueWrapper(ValueWrapper):
    def get_value_sql(self, ctx: SqlContext) -> str:
        if isinstance(self.value, bool):
            return "1" if self.value else "0"
        return super().get_value_sql(ctx)


class SQLLiteQuery(Query):
    """
    Defines a query class for use with Microsoft SQL Server.
    """

    SQL_CONTEXT = DEFAULT_SQL_CONTEXT.copy(dialect=Dialects.SQLITE)

    @classmethod
    def _builder(cls, **kwargs: Any) -> SQLLiteQueryBuilder:
        return SQLLiteQueryBuilder(**kwargs)


class SQLLiteQueryBuilder(QueryBuilder):
    QUERY_CLS = SQLLiteQuery

    def __init__(self, **kwargs) -> None:
        super().__init__(wrapper_cls=SQLLiteValueWrapper, **kwargs)
        self._returns: list[Term] = []
        self._return_star = False

    def __copy__(self):
        newone = super().__copy__()
        newone._returns = copy(self._returns)
        return newone

    @builder
    def returning(self, *terms: Any) -> SQLLiteQueryBuilder:  # type:ignore[return]
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
                itertools.chain.from_iterable([j.criterion.tables_ for j in self._joins])  # type:ignore[attr-defined]
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

    def _return_field(self, term: str | Field) -> None:
        if self._return_star:
            return

        self._validate_returning_term(term)  # type:ignore[arg-type]

        if isinstance(term, Star):
            self._set_returns_for_star()

        self._returns.append(term)  # type:ignore[arg-type]

    def _return_field_str(self, term: str | Field) -> None:
        if term == "*":
            self._set_returns_for_star()
            self._returns.append(Star())
            return

        if self._insert_table:
            table = self._insert_table
        elif self._update_table:
            table = self._update_table
        elif self._delete_from:
            table = self._from[0]
        else:
            raise QueryException("Returning can't be used in this query")
        self._return_field(Field(term, table=table))  # type:ignore[arg-type]

    def _return_other(self, function: Term) -> None:
        self._validate_returning_term(function)
        self._returns.append(function)

    def _returning_sql(self, ctx: SqlContext) -> str:
        returning_ctx = ctx.copy(with_alias=True)
        return " RETURNING {returning}".format(
            returning=",".join(term.get_sql(returning_ctx) for term in self._returns),
        )

    def get_sql(self, ctx: SqlContext | None = None) -> str:
        ctx = ctx or SQLLiteQuery.SQL_CONTEXT
        if not (self._selects or self._insert_table or self._delete_from or self._update_table):
            return ""
        if self._insert_table and not (self._selects or self._values or self._default_values):
            return ""
        if self._update_table and not self._updates:
            return ""

        has_joins = bool(self._joins)
        has_multiple_from_clauses = len(self._from) > 1
        has_subquery_from_clause = len(self._from) > 0 and isinstance(self._from[0], QueryBuilder)
        has_reference_to_foreign_table = self._foreign_table
        has_update_from = self._update_table and self._from

        ctx = ctx.copy(
            with_namespace=any(
                [
                    has_joins,
                    has_multiple_from_clauses,
                    has_subquery_from_clause,
                    has_reference_to_foreign_table,
                    has_update_from,
                ]
            ),
        )
        if self._update_table:
            querystring = self._with_sql(ctx) if self._with else ""

            querystring += self._update_sql(ctx)
            querystring += self._set_sql(ctx)

            if self._joins:
                self._from.append(self._update_table.as_(self._update_table.get_table_name() + "_"))

            if self._from:
                querystring += self._from_sql(ctx)
            if self._joins:
                querystring += " " + " ".join(join.get_sql(ctx) for join in self._joins)

            if self._wheres:
                querystring += self._where_sql(ctx)

            if self._orderbys:
                querystring += self._orderby_sql(ctx)
            if self._limit:
                querystring += self._limit_sql(ctx)
        else:
            querystring = super().get_sql(ctx=ctx)
        if self._returns:
            returning_ctx = ctx.copy(with_namespace=self._update_table and self.from_)
            querystring += self._returning_sql(returning_ctx)
        return querystring
