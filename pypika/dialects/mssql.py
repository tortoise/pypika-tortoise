from __future__ import annotations

from typing import Any, cast

from pypika.enums import Dialects
from pypika.exceptions import QueryException
from pypika.queries import Query, QueryBuilder
from pypika.terms import ValueWrapper
from pypika.utils import builder


class MSSQLQuery(Query):
    """
    Defines a query class for use with Microsoft SQL Server.
    """

    @classmethod
    def _builder(cls, **kwargs: Any) -> "MSSQLQueryBuilder":
        return MSSQLQueryBuilder(**kwargs)


class MSSQLQueryBuilder(QueryBuilder):
    QUERY_CLS = MSSQLQuery

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(dialect=Dialects.MSSQL, **kwargs)
        self._top: int | None = None

    @builder
    def top(self, value: str | int) -> MSSQLQueryBuilder:  # type:ignore[return]
        """
        Implements support for simple TOP clauses.

        Does not include support for PERCENT or WITH TIES.

        https://docs.microsoft.com/en-us/sql/t-sql/queries/top-transact-sql?view=sql-server-2017
        """
        try:
            self._top = int(value)
        except ValueError:
            raise QueryException("TOP value must be an integer") from None

    @builder
    def fetch_next(self, limit: int) -> MSSQLQueryBuilder:  # type:ignore[return]
        # Overridden to provide a more domain-specific API for T-SQL users
        self._limit = cast(ValueWrapper, self.wrap_constant(limit))

    def _offset_sql(self, **kwargs) -> str:
        order_by = ""
        if not self._orderbys:
            order_by = " ORDER BY (SELECT 0)"
        return order_by + " OFFSET {offset} ROWS".format(
            offset=self._offset.get_sql(**kwargs) if self._offset is not None else 0
        )

    def _limit_sql(self, **kwargs) -> str:
        if self._limit is None:
            return ""
        return " FETCH NEXT {limit} ROWS ONLY".format(limit=self._limit.get_sql(**kwargs))

    def _apply_pagination(self, querystring: str, **kwargs) -> str:
        # Note: Overridden as MSSQL specifies offset before the fetch next limit
        if self._limit is not None or self._offset:
            # Offset has to be present if fetch next is specified in a MSSQL query
            querystring += self._offset_sql(**kwargs)

        if self._limit is not None:
            querystring += self._limit_sql(**kwargs)

        return querystring

    def get_sql(self, *args: Any, **kwargs: Any) -> str:
        # MSSQL does not support group by a field alias.
        # Note: set directly in kwargs as they are re-used down the tree in the case of subqueries!
        kwargs["groupby_alias"] = False
        return super().get_sql(*args, **kwargs)

    def _top_sql(self) -> str:
        return "TOP ({}) ".format(self._top) if self._top else ""

    def _select_sql(self, **kwargs: Any) -> str:
        return "SELECT {distinct}{top}{select}".format(
            top=self._top_sql(),
            distinct="DISTINCT " if self._distinct else "",
            select=",".join(
                term.get_sql(with_alias=True, subquery=True, **kwargs) for term in self._selects
            ),
        )
