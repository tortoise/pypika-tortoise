from typing import Any

from pypika.enums import Dialects
from pypika.queries import Query, QueryBuilder
from pypika.terms import ValueWrapper


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
