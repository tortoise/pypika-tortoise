"""
Package for SQL functions wrappers
"""

from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING, Any

from .context import SqlContext
from .enums import Dialects, SqlTypes
from .exceptions import DialectNotSupported
from .terms import AggregateFunction, Function, Star, Term, ValueWrapper
from .utils import builder

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class DistinctOptionFunction(AggregateFunction):
    def __init__(self, name: str, *args, **kwargs) -> None:
        alias = kwargs.get("alias")
        super().__init__(name, *args, alias=alias)
        self._distinct = False

    def get_function_sql(self, ctx: SqlContext) -> str:
        s = super().get_function_sql(ctx)

        n = len(self.name) + 1
        if self._distinct:
            return s[:n] + "DISTINCT " + s[n:]
        return s

    @builder
    def distinct(self) -> Self:  # type:ignore[return]
        self._distinct = True


class Count(DistinctOptionFunction):
    def __init__(self, param: Any, alias: str | None = None) -> None:
        is_star = isinstance(param, str) and param == "*"
        super().__init__("COUNT", Star() if is_star else param, alias=alias)


# Arithmetic Functions
class Sum(DistinctOptionFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("SUM", term, alias=alias)


class Avg(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("AVG", term, alias=alias)


class Min(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("MIN", term, alias=alias)


class Max(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("MAX", term, alias=alias)


class Std(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("STD", term, alias=alias)


class StdDev(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("STDDEV", term, alias=alias)


class Abs(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("ABS", term, alias=alias)


class First(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("FIRST", term, alias=alias)


class Last(AggregateFunction):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("LAST", term, alias=alias)


class Sqrt(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("SQRT", term, alias=alias)


class Floor(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("FLOOR", term, alias=alias)


class ApproximatePercentile(AggregateFunction):
    def __init__(self, term: Any, percentile: int | float | str, alias: str | None = None) -> None:
        super().__init__("APPROXIMATE_PERCENTILE", term, alias=alias)
        self.percentile = float(percentile)

    def get_special_params_sql(self, ctx: SqlContext) -> str:
        return f"USING PARAMETERS percentile={self.percentile}"


# Type Functions
class Cast(Function):
    def __init__(self, term: Any, as_type: Any, alias: str | None = None) -> None:
        super().__init__("CAST", term, alias=alias)
        self.as_type = as_type

    def get_special_params_sql(self, ctx: SqlContext) -> str:
        type_sql = (
            self.as_type.get_sql(ctx)
            if hasattr(self.as_type, "get_sql")
            else str(self.as_type).upper()
        )

        return "AS {type}".format(type=type_sql)


class Convert(Function):
    def __init__(self, term: Any, encoding: Enum, alias: str | None = None) -> None:
        super().__init__("CONVERT", term, alias=alias)
        self.encoding = encoding

    def get_special_params_sql(self, ctx: SqlContext) -> str:
        return "USING {type}".format(type=self.encoding.value)


class ToChar(Function):
    def __init__(self, term: Any, as_type: Any, alias: str | None = None) -> None:
        super().__init__("TO_CHAR", term, as_type, alias=alias)


class Signed(Cast):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__(term, SqlTypes.SIGNED, alias=alias)


class Unsigned(Cast):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__(term, SqlTypes.UNSIGNED, alias=alias)


class Date(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("DATE", term, alias=alias)


class DateDiff(Function):
    def __init__(
        self, interval: Any, start_date: Any, end_date: Any, alias: str | None = None
    ) -> None:
        super().__init__("DATEDIFF", interval, start_date, end_date, alias=alias)


class TimeDiff(Function):
    def __init__(self, start_time: Any, end_time: Any, alias: str | None = None) -> None:
        super().__init__("TIMEDIFF", start_time, end_time, alias=alias)


class DateAdd(Function):
    def __init__(self, date_part: Any, interval: Any, term: Any, alias: str | None = None) -> None:
        super().__init__("DATE_ADD", date_part, interval, term, alias=alias)


class ToDate(Function):
    def __init__(self, value: Any, format_mask: Any, alias: str | None = None) -> None:
        super().__init__("TO_DATE", value, format_mask, alias=alias)


class Timestamp(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("TIMESTAMP", term, alias=alias)


class TimestampAdd(Function):
    def __init__(self, date_part: Any, interval: Any, term: Any, alias: str | None = None) -> None:
        super().__init__("TIMESTAMPADD", date_part, interval, term, alias=alias)


# String Functions
class Ascii(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("ASCII", term, alias=alias)


class NullIf(Function):
    def __init__(self, term: Any, condition: Any, **kwargs) -> None:
        super().__init__("NULLIF", term, condition, **kwargs)


class Bin(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("BIN", term, alias=alias)


class Concat(Function):
    def __init__(self, *terms, **kwargs) -> None:
        super().__init__("CONCAT", *terms, **kwargs)


class Insert(Function):
    def __init__(
        self, term: Any, start: Any, stop: Any, subterm: Any, alias: str | None = None
    ) -> None:
        term, start, stop, subterm = [term for term in (term, start, stop, subterm)]
        super().__init__("INSERT", term, start, stop, subterm, alias=alias)


class Length(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("LENGTH", term, alias=alias)


class Upper(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("UPPER", term, alias=alias)


class Lower(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("LOWER", term, alias=alias)


class Substring(Function):
    def __init__(self, term: Any, start: Any, stop: Any, alias: str | None = None) -> None:
        super().__init__("SUBSTRING", term, start, stop, alias=alias)


class Reverse(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("REVERSE", term, alias=alias)


class Trim(Function):
    def __init__(self, term: Any, trim_chars: str = " ", alias: str | None = None) -> None:
        args = [term]
        if trim_chars != " ":
            args.append(ValueWrapper(trim_chars, allow_parametrize=False))

        super().__init__("TRIM", *args, alias=alias)

    def get_function_sql(self, ctx: SqlContext) -> str:
        if len(self.args) == 1:
            return super().get_function_sql(ctx)

        args_sql = [self.get_arg_sql(arg, ctx) for arg in self.args]
        if ctx.dialect == Dialects.SQLITE:
            args = ",".join(args_sql)
        else:
            args = f"BOTH {args_sql[1]} FROM {args_sql[0]}"

        return "{name}({args})".format(
            name=self.get_dialect_special_name(ctx.dialect) or self.name,
            args=args,
        )


class LTrim(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("LTRIM", term, alias=alias)


class RTrim(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("RTRIM", term, alias=alias)


class _Pad(Function):
    db_function: str

    def __init__(
        self, term: Any, length: int, fill_text: str = " ", alias: str | None = None
    ) -> None:
        super().__init__(
            self.db_function,
            term,
            ValueWrapper(length, allow_parametrize=False),
            ValueWrapper(fill_text, allow_parametrize=False),
            alias=alias,
        )

    def get_sql(self, ctx: SqlContext) -> str:
        if ctx.dialect == Dialects.SQLITE:
            raise DialectNotSupported(f"{self.db_function} is not supported in SQLite.")

        return super().get_sql(ctx)


class LPad(_Pad):
    db_function = "LPAD"


class RPad(_Pad):
    db_function = "RPAD"


class Replace(Function):
    def __init__(self, term: Any, search: str, replacement: str, alias: str | None = None) -> None:
        super().__init__(
            "REPLACE",
            term,
            ValueWrapper(search, allow_parametrize=False),
            ValueWrapper(replacement, allow_parametrize=False),
            alias=alias,
        )


class SplitPart(Function):
    def __init__(self, term: Any, delimiter: Any, index: Any, alias: str | None = None) -> None:
        super().__init__("SPLIT_PART", term, delimiter, index, alias=alias)


class RegexpMatches(Function):
    def __init__(self, term: Any, pattern: Any, modifiers=None, alias: str | None = None) -> None:
        super().__init__("REGEXP_MATCHES", term, pattern, modifiers, alias=alias)


class RegexpLike(Function):
    def __init__(self, term: Any, pattern: Any, modifiers=None, alias: str | None = None) -> None:
        super().__init__("REGEXP_LIKE", term, pattern, modifiers, alias=alias)


# Date/Time Functions
class Now(Function):
    def __init__(self, alias: str | None = None) -> None:
        super().__init__("NOW", alias=alias)


class UtcTimestamp(Function):
    def __init__(self, alias: str | None = None) -> None:
        super().__init__("UTC_TIMESTAMP", alias=alias)


class CurTimestamp(Function):
    def __init__(self, alias: str | None = None) -> None:
        super().__init__("CURRENT_TIMESTAMP", alias=alias)

    def get_function_sql(self, ctx: SqlContext) -> str:
        # CURRENT_TIMESTAMP takes no arguments, so the SQL to generate is quite
        # simple.  Note that empty parentheses have been omitted intentionally.
        return "CURRENT_TIMESTAMP"


class CurDate(Function):
    def __init__(self, alias: str | None = None) -> None:
        super().__init__("CURRENT_DATE", alias=alias)


class CurTime(Function):
    def __init__(self, alias: str | None = None) -> None:
        super().__init__("CURRENT_TIME", alias=alias)


class Extract(Function):
    def __init__(self, date_part: Any, field: Term, alias: str | None = None) -> None:
        super().__init__("EXTRACT", date_part, alias=alias)
        self.field = field

    def get_special_params_sql(self, ctx: SqlContext) -> str:
        return "FROM {field}".format(field=self.field.get_sql(ctx))


# Null Functions
class IsNull(Function):
    def __init__(self, term: Any, alias: str | None = None) -> None:
        super().__init__("ISNULL", term, alias=alias)


class Coalesce(Function):
    def __init__(self, term: Any, *default_values, **kwargs) -> None:
        super().__init__("COALESCE", term, *default_values, **kwargs)


class IfNull(Function):
    def __init__(self, condition: Any, term: Any, **kwargs) -> None:
        super().__init__("IFNULL", condition, term, **kwargs)


class NVL(Function):
    def __init__(self, condition, term, alias: str | None = None) -> None:
        super().__init__("NVL", condition, term, alias=alias)
