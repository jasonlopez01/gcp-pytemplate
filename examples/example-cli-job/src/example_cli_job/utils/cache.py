from datetime import datetime, timedelta, timezone
from functools import lru_cache, wraps
from typing import Any, Callable

"""
Based on below
https://realpython.com/lru-cache-python/
"""


def timed_lru_cache(seconds: int = 300, maxsize: int = 50):
    """Function wrapper to expand functionality of functools.lru_cache, by adding timeout to the cache

    :param seconds: lifetime of cache in seconds (entire cache expires after X seconds)
    :param maxsize: maximum size of cache, ie number of unique key-values in cache, new values replacing oldest ones
    :return:
    """

    def wrapper_cache(func: Callable) -> Callable:
        # Wrap the function with standard lru_cache
        cached_func = lru_cache(maxsize=maxsize)(func)
        lifetime = timedelta(seconds=seconds)
        expiration = datetime.now(timezone.utc) + lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            nonlocal expiration
            if datetime.now(timezone.utc) >= expiration:
                cached_func.cache_clear()
                expiration = datetime.now(timezone.utc) + lifetime

            return cached_func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


def make_hashable(function: Callable):
    """Function wrapper to convert any List or Set input args to hashable versions (tuple or frozenset).

    Can be used with functools.lru_cache function decorator to make a function with mutable inputs cache-able

    :param function:
    :return:
    """

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any):
        new_args = tuple(frozenset(x) if isinstance(x, (list, set)) else x for x in args)
        new_kwargs = {k: frozenset(v) if isinstance(v, (list, set)) else v for k, v in kwargs.items()}
        return function(*new_args, **new_kwargs)

    return wrapper