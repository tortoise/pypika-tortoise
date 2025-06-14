from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SqlContext:
    """Represents the context for get_sql() methods to determine how to render SQL."""

    quote_char: str
    secondary_quote_char: str
    alias_quote_char: str
    dialect: Dialects
    as_keyword: bool = False
    subquery: bool = False
    with_alias: bool = False
    with_namespace: bool = False
    subcriterion: bool = False
    parameterizer: Parameterizer | None = None
    groupby_alias: bool = True
    orderby_alias: bool = True

    def copy(self, **kwargs) -> SqlContext:
        cls = self.__class__
        fields = cls.__dataclass_fields__
        return cls(**{f: kwargs.get(f, getattr(self, f)) for f in fields})


from .enums import Dialects  # noqa: E402

DEFAULT_SQL_CONTEXT = SqlContext(
    quote_char='"',
    secondary_quote_char="'",
    alias_quote_char="",
    as_keyword=False,
    dialect=Dialects.SQLITE,
)

from .terms import Parameterizer  # noqa: E402
