from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from example_cli_job.utils.cache import make_hashable, timed_lru_cache


class TestTimedLruCache:
    def test_returns_cached_value_within_lifetime(self):
        call_count = 0

        @timed_lru_cache(seconds=60)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive(5) == 10
        assert expensive(5) == 10
        assert call_count == 1

    def test_different_args_produce_different_results(self):
        call_count = 0

        @timed_lru_cache(seconds=60)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive(5) == 10
        assert expensive(3) == 6
        assert call_count == 2

    def test_cache_expires_after_lifetime(self):
        call_count = 0

        @timed_lru_cache(seconds=10)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        now = datetime.now(UTC)

        with patch("example_cli_job.utils.cache.datetime") as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            # Reset expiration to a known time by calling once
            expensive(5)
            assert call_count == 1

            # Advance time past the lifetime
            mock_dt.now.return_value = now + timedelta(seconds=11)
            expensive(5)
            assert call_count == 2

    def test_maxsize_limits_cache_entries(self):
        call_count = 0

        @timed_lru_cache(seconds=300, maxsize=2)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        expensive(1)
        expensive(2)
        expensive(3)  # evicts 1
        assert call_count == 3

        expensive(1)  # must recompute
        assert call_count == 4

    def test_works_with_keyword_arguments(self):
        call_count = 0

        @timed_lru_cache(seconds=60)
        def expensive(x, y=10):
            nonlocal call_count
            call_count += 1
            return x + y

        assert expensive(1, y=10) == 11
        assert expensive(1, y=10) == 11
        assert call_count == 1

        assert expensive(1, y=20) == 21
        assert call_count == 2


class TestMakeHashable:
    def test_converts_list_args_to_frozenset(self):
        received_args = []

        @make_hashable
        def func(*args, **kwargs):
            received_args.append((args, kwargs))
            return args

        func([1, 2, 3])
        assert isinstance(received_args[0][0][0], frozenset)
        assert received_args[0][0][0] == frozenset({1, 2, 3})

    def test_converts_set_args_to_frozenset(self):
        received_args = []

        @make_hashable
        def func(*args, **kwargs):
            received_args.append((args, kwargs))
            return args

        func({1, 2, 3})
        assert isinstance(received_args[0][0][0], frozenset)
        assert received_args[0][0][0] == frozenset({1, 2, 3})

    def test_converts_list_kwargs_to_frozenset(self):
        received_kwargs = {}

        @make_hashable
        def func(**kwargs):
            received_kwargs.update(kwargs)

        func(items=[4, 5, 6])
        assert isinstance(received_kwargs["items"], frozenset)
        assert received_kwargs["items"] == frozenset({4, 5, 6})

    def test_converts_set_kwargs_to_frozenset(self):
        received_kwargs = {}

        @make_hashable
        def func(**kwargs):
            received_kwargs.update(kwargs)

        func(items={4, 5, 6})
        assert isinstance(received_kwargs["items"], frozenset)
        assert received_kwargs["items"] == frozenset({4, 5, 6})

    def test_leaves_non_list_set_args_unchanged(self):
        received_args = []

        @make_hashable
        def func(*args):
            received_args.append(args)

        func("hello", 42, (1, 2))
        assert received_args[0] == ("hello", 42, (1, 2))

    def test_mixed_args_only_converts_lists_and_sets(self):
        received_args = []

        @make_hashable
        def func(*args, **kwargs):
            received_args.append((args, kwargs))

        func("key", [1, 2], value="str", tags={3, 4})
        args, kwargs = received_args[0]
        assert args[0] == "key"
        assert isinstance(args[1], frozenset)
        assert kwargs["value"] == "str"
        assert isinstance(kwargs["tags"], frozenset)

    def test_works_with_lru_cache(self):
        call_count = 0

        @make_hashable
        @timed_lru_cache(seconds=60)
        def expensive(items):
            nonlocal call_count
            call_count += 1
            return len(items)

        assert expensive([1, 2, 3]) == 3
        assert expensive([1, 2, 3]) == 3
        assert call_count == 1

        assert expensive({1, 2, 3}) == 3
        assert expensive({1, 2, 3}) == 3
        assert call_count == 1  # Should still be 1 as frozenset({1,2,3}) is the same