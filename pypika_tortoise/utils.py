from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar, overload

from .context import SqlContext

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Concatenate, ParamSpec
    else:
        from typing import Concatenate

        from typing_extensions import ParamSpec

    P = ParamSpec("P")


T_Retval = TypeVar("T_Retval")
T_Self = TypeVar("T_Self")


@overload
def builder(
    func: Callable[Concatenate[T_Self, P], None],
) -> Callable[Concatenate[T_Self, P], T_Self]: ...


@overload
def builder(
    func: Callable[Concatenate[T_Self, P], T_Retval],
) -> Callable[Concatenate[T_Self, P], T_Retval]: ...


def builder(
    func: Callable[Concatenate[T_Self, P], T_Retval | None],
) -> Callable[Concatenate[T_Self, P], T_Retval | T_Self]:
    """
    Decorator for wrapper "builder" functions.  These are functions on the Query class or other classes used for
    building queries which mutate the query and return self.  To make the build functions immutable, this decorator is
    used which will deepcopy the current instance.  This decorator will return the return value of the inner function
    or the new copy of the instance.  The inner function does not need to return self.
    """
    import copy

    @wraps(func)
    def _copy(self: T_Self, *args: P.args, **kwargs: P.kwargs) -> T_Retval | T_Self:
        self_copy = copy.copy(self) if getattr(self, "immutable", True) else self
        result = func(self_copy, *args, **kwargs)

        # Return self if the inner function returns None.  This way the inner function can return something
        # different (for example when creating joins, a different builder is returned).
        if result is None:
            return self_copy

        return result

    return _copy


def ignore_copy(func: Callable[[T_Self, str], T_Retval]) -> Callable[[T_Self, str], T_Retval]:
    """
    Decorator for wrapping the __getattr__ function for classes that are copied via deepcopy.  This prevents infinite
    recursion caused by deepcopy looking for magic functions in the class. Any class implementing __getattr__ that is
    meant to be deepcopy'd should use this decorator.

    deepcopy is used by pypika in builder functions (decorated by @builder) to make the results immutable.  Any data
    model type class (stored in the Query instance) is copied.
    """

    def _getattr(self: T_Self, name: str) -> T_Retval:
        if name in (
            "__copy__",
            "__deepcopy__",
            "__getstate__",
            "__setstate__",
            "__getnewargs__",
        ):
            raise AttributeError(
                "'%s' object has no attribute '%s'" % (self.__class__.__name__, name)
            )

        return func(self, name)

    return _getattr


def resolve_is_aggregate(values: list[bool | None]) -> bool | None:
    """
    Resolves the is_aggregate flag for an expression that contains multiple terms.  This works like a voter system,
    each term votes True or False or abstains with None.

    :param values: A list of booleans (or None) for each term in the expression
    :return: If all values are True or None, True is returned.  If all values are None, None is returned. Otherwise,
        False is returned.
    """
    result = [x for x in values if x is not None]
    if result:
        return all(result)
    return None


def format_quotes(value: Any, quote_char: str | None) -> str:
    return "{quote}{value}{quote}".format(value=value, quote=quote_char or "")


def format_alias_sql(
    sql: str,
    alias: str | None,
    ctx: SqlContext,
) -> str:
    if alias is None:
        return sql
    return "{sql}{_as}{alias}".format(
        sql=sql,
        _as=" AS " if ctx.as_keyword else " ",
        alias=format_quotes(alias, ctx.alias_quote_char or ctx.quote_char),
    )


def validate(*args: Any, exc: Exception | None = None, type: type | None = None) -> None:
    if type is not None:
        for arg in args:
            if not isinstance(arg, type):
                raise exc  # type:ignore[misc]
